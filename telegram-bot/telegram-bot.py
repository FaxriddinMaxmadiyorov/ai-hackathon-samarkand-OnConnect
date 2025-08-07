import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import re
import os
from telegram.ext import MessageHandler, filters
from dotenv import load_dotenv

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
        user_data = context.user_data

        # Increment session_id each time user sends /start
        user_data['session_id'] = user_data.get('session_id', 0) + 1

        """Start the medical consultation and ask for name."""
        await update.message.reply_text(
            "Welcome to the Medical Consultation System!\n\n"
            "I will collect the necessary medical information.\n\n"
            "You can cancel the process anytime by typing /cancel\n\n"
            "Please attach Patient DATA?"
        )
        return PATIENT_DATA

    async def get_patient_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Excel file uploads and save them under data/{user_id}/{session_id}/test_results/."""
        document = update.message.document
        user_id = update.effective_user.id

        if document is None:
            await update.message.reply_text("❌ Please send an Excel file (.xlsx or .xls format).")
            return PATIENT_DATA

        # Check if the file is an Excel file
        if not document.file_name.lower().endswith(('.xlsx', '.xls')):
            await update.message.reply_text(
                "❌ Please send an Excel file (.xlsx or .xls format)."
            )
            return PATIENT_DATA  # Stay in same state

        try:
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

            # Save path if needed
            context.user_data["patient_data_path"] = file_path

            # Confirm to user
            await update.message.reply_text(
                f"✅ Excel file saved successfully!\n\n"
                f"📄 *File name:* `{os.path.basename(file_path)}`\n"
                f"📁 *Saved to:* `{file_path}`",
                parse_mode="Markdown"
            )

            logger.info(f"Excel file saved: {file_path} for user {user_id}, session {session_id}")

            await update.message.reply_text("🧬 Here is output:")
            return LIST_OF_DOCTORS

        except Exception as e:
            logger.error(f"Error saving Excel file: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error saving your Excel file. Please try again."
            )
            return PATIENT_DATA  # Stay in same state on failure
    
    async def invalid_test_result_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Please upload your test results as an Excel file (.xlsx or .xls).")
        return PATIENT_DATA
    
    async def return_list_of_doctors(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        message = """
        await update.message.reply_text(message)
        
        return ConversationHandler.END

    async def new_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start a new data collection session."""
        # Clear previous data
        context.user_data.clear()
        
        await update.message.reply_text(
            "Starting a new medical consultation!\n\n"
            "Please attach the Patient DATA file.",
        )
        return PATIENT_DATA

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        await update.message.reply_text(
            "Medical consultation cancelled.\n\n"
            "Commands:\n"
            "/start - Start again\n"
            "/help - Help",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display help information."""
        help_text = (
            "**MEDICAL CONSULTATION SYSTEM**\n\n"
            "**Available commands:**\n"
            "• /start - Start consultation\n"
            "• /new - New patient\n"
            "• /cancel - Cancel current session\n"
            "• /help - Help\n\n"
            "After collecting all data, you can start a new consultation!"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    def run(self):
        """Start the bot."""
        logger.info("Starting Medical Consultation Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

# Main execution
if __name__ == '__main__':
    bot = MedicalConsultationBot(bot_token)
    bot.run()