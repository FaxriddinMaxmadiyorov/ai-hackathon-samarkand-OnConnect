import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import re
import os
from telegram.ext import MessageHandler, filters
from dotenv import load_dotenv
import recommendation

# Load environment variables
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
(PATIENT_DATA, LIST_OF_DOCTORS) = range(2)

class MedicalConsultationBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        # Conversation handler for data collection
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                PATIENT_DATA: [
                    MessageHandler(filters.Document.ALL, self.get_patient_data),  # handles file uploads
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.invalid_test_result_input),  # fallback for non-files
                ],
                LIST_OF_DOCTORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.return_list_of_doctors)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('new', self.new_collection))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the medical consultation and ask for patient data."""
        user_data = context.user_data

        # Increment session_id each time user sends /start
        user_data['session_id'] = user_data.get('session_id', 0) + 1

        await update.message.reply_text(
            "🏥 **Welcome to the Medical Consultation System!**\n\n"
            "I will help you find the most appropriate doctors based on your medical data.\n\n"
            "📋 **Instructions:**\n"
            "• Upload your patient data as an Excel file (.csv)\n"
            "• I'll analyze your data and recommend 3 suitable doctors\n\n"
            "You can cancel the process anytime by typing /cancel\n\n"
            "📤 **Please attach your Patient DATA Excel file:**",
            parse_mode="Markdown"
        )
        return PATIENT_DATA

    async def get_patient_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Excel file uploads and process them for doctor recommendations."""
        document = update.message.document
        user_id = update.effective_user.id

        if document is None:
            await update.message.reply_text("❌ Please send an Excel file (.csv format).")
            return PATIENT_DATA

        # Check if the file is an Excel file
        if not document.file_name.lower().endswith(('.csv')):
            await update.message.reply_text(
                "❌ Please send an Excel file (.csv format)."
            )
            return PATIENT_DATA  # Stay in same state

        try:
            # Show processing message
            processing_msg = await update.message.reply_text(
                "⏳ **Processing your patient data...**\n"
                "Please wait while I analyze your file and find suitable doctors.",
                parse_mode="Markdown"
            )

            # Get or set session ID
            session_id = context.user_data.get("session_id", 1)

            # Download file object from Telegram
            file = await context.bot.get_file(document.file_id)

            # Create structured directory
            directory_path = f"data/{user_id}/{session_id}/patient_data"
            os.makedirs(directory_path, exist_ok=True)

            # Prepare file path with collision check
            original_name = document.file_name
            name, ext = os.path.splitext(original_name)
            file_path = os.path.join(directory_path, original_name)

            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(directory_path, f"{name}_{counter}{ext}")
                counter += 1

            # Download file to target location
            await file.download_to_drive(file_path)

            # Save path for later use
            context.user_data["patient_data_path"] = file_path

            # Delete processing message
            await processing_msg.delete()

            # Confirm file upload
            await update.message.reply_text(
                f"✅ **Excel file received successfully!**\n\n"
                f"📄 **File name:** `{os.path.basename(file_path)}`\n"
                f"📁 **Saved to:** `{file_path}`\n\n"
                "🔍 **Analyzing your data and finding suitable doctors...**",
                parse_mode="Markdown"
            )

            logger.info(f"Excel file saved: {file_path} for user {user_id}, session {session_id}")

            # Process the file and get doctor recommendations
            try:
                recommendations = recommendation.get_recommendations(file_path)
                
                # Store recommendations in user data
                context.user_data["recommendations"] = recommendations
                
                # Send the recommendations
                await update.message.reply_text(
                    "🩺 **Doctor Recommendations Based on Your Medical Data:**\n\n" +
                    f"{recommendations}\n\n" +
                    "💡 **Next Steps:**\n"
                    "• Contact the recommended doctors\n"
                    "• Schedule appointments based on availability\n"
                    "• Bring your medical records to the consultation\n\n"
                    "🔄 Use /new to analyze another patient file\n"
                    "❓ Use /help for more information"
                )
                
                return ConversationHandler.END
                
            except Exception as e:
                logger.error(f"Error getting recommendations: {e}")
                await update.message.reply_text(
                    "❌ **Error processing your medical data.**\n\n"
                    "There was an issue analyzing your file or connecting to the recommendation system. "
                    "Please make sure your Excel file contains valid medical data and try again.\n\n"
                    f"**Error details:** {str(e)}\n\n"
                    "🔄 Use /new to try again with a different file"
                )
                return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error saving Excel file: {e}")
            await update.message.reply_text(
                "❌ **Sorry, there was an error processing your Excel file.**\n\n"
                "Please make sure the file is a valid Excel format (.csv) and try again.\n\n"
                f"**Error details:** {str(e)}"
            )
            return PATIENT_DATA  # Stay in same state on failure
    
    async def invalid_test_result_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle invalid input when expecting a file."""
        await update.message.reply_text(
            "❌ **Please upload your patient data as an Excel file (.csv).**\n\n"
            "📋 **Instructions:**\n"
            "• Use the 📎 attachment button in Telegram\n"
            "• Select your Excel file with patient data\n"
            "• Send the file to continue\n\n"
            "🔄 Use /cancel to stop or /help for more information"
        )
        return PATIENT_DATA
    
    async def return_list_of_doctors(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Return the list of recommended doctors (fallback state)."""
        recommendations = context.user_data.get("recommendations", "No recommendations available.")
        
        await update.message.reply_text(
            "🩺 **Your Doctor Recommendations:**\n\n" +
            f"{recommendations}\n\n" +
            "🔄 Use /new to analyze another patient file"
        )
        
        return ConversationHandler.END

    async def new_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start a new data collection session."""
        # Clear previous data but keep session counter
        session_id = context.user_data.get('session_id', 0)
        context.user_data.clear()
        context.user_data['session_id'] = session_id + 1
        
        await update.message.reply_text(
            "🔄 **Starting a new medical consultation!**\n\n"
            "📤 **Please attach your Patient DATA Excel file:**",
            parse_mode="Markdown"
        )
        return PATIENT_DATA

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        await update.message.reply_text(
            "❌ **Medical consultation cancelled.**\n\n"
            "**Available Commands:**\n"
            "• /start - Start new consultation\n"
            "• /new - New patient analysis\n"
            "• /help - Get help information",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display help information."""
        help_text = (
            "🏥 **MEDICAL CONSULTATION SYSTEM**\n\n"
            "**Available Commands:**\n"
            "• `/start` - Start new consultation\n"
            "• `/new` - Analyze another patient file\n"
            "• `/cancel` - Cancel current session\n"
            "• `/help` - Show this help message\n\n"
            "**How it works:**\n"
            "1️⃣ Send `/start` to begin\n"
            "2️⃣ Upload your patient data Excel file (.csv)\n"
            "3️⃣ Get personalized doctor recommendations\n"
            "4️⃣ Contact the recommended doctors\n\n"
            "**File Requirements:**\n"
            "• Excel format (.csv)\n"
            "• Contains patient medical information\n"
            "• Properly structured data\n\n"
            "**Features:**\n"
            "• AI-powered doctor matching\n"
            "• Personalized recommendations\n"
            "• Secure file handling\n"
            "• Multiple consultation sessions\n\n"
            "🔒 **Privacy:** Your files are stored securely and used only for generating recommendations."
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    def run(self):
        """Start the bot."""
        logger.info("Starting Medical Consultation Bot...")
        print("🏥 Medical Consultation Bot is starting...")
        print("📋 Bot will help users find appropriate doctors based on medical data")
        print("🔄 Press Ctrl+C to stop the bot")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

# Main execution
if __name__ == '__main__':
    if not bot_token:
        print("❌ Error: BOT_TOKEN not found in environment variables!")
        print("Please make sure you have a .env file with BOT_TOKEN=your_bot_token")
        exit(1)
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Check if doctors.csv exists
    if not os.path.exists('data/doctors.csv'):
        print("⚠️  Warning: data/doctors.csv not found. Using sample doctor data.")
        print("💡 Tip: Create data/doctors.csv with your doctor database for better results.")
    
    try:
        bot = MedicalConsultationBot(bot_token)
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logger.error(f"Bot startup error: {e}")