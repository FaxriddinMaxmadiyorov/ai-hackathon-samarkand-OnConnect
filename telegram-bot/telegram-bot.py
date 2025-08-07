import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import re
import os
from telegram.ext import MessageHandler, filters

BASE_FILE_DIR = 'data'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
(NAME, SEX, DATE_OF_BIRTH, LOCATION, MEDICINE, 
 WEIGHT, HEIGHT, COMPLAINTS, MEDICAL_HISTORY, TEST_RESULTS, DIAGNOSIS) = range(11)

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
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_name)],
                SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_sex)],
                DATE_OF_BIRTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_date_of_birth)],
                LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_location)],
                MEDICINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_medicine)],
                WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_weight)],
                HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_height)],
                COMPLAINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_complaints)],
                MEDICAL_HISTORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_medical_history)],
                TEST_RESULTS: [
                    MessageHandler(filters.Document.ALL, self.get_test_results),  # handles file uploads
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.invalid_test_result_input),  # fallback for non-files
                ],

                DIAGNOSIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_diagnosis)]
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
            "What's your full name?"
        )
        return NAME

    async def get_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store name and ask for sex."""
        user_data = context.user_data
        user_data['name'] = update.message.text.strip()
        
        # Create keyboard for sex selection
        reply_keyboard = [['Мужской / Male', 'Женский / Female'], ['Другое / Other']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"Thank you, {user_data['name']}! 👋\n\n"
            "Please specify your sex:",
            reply_markup=markup
        )
        return SEX

    async def get_sex(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store sex and ask for date of birth."""
        user_data = context.user_data
        user_data['sex'] = update.message.text.strip()
        
        await update.message.reply_text(
            "Please enter your date of birth (format: DD.MM.YYYY or DD/MM/YYYY)\n\n",
            reply_markup=ReplyKeyboardRemove()
        )
        return DATE_OF_BIRTH

    async def get_date_of_birth(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store date of birth and ask for location."""
        user_data = context.user_data
        dob_text = update.message.text.strip()
        
        # Validate date format
        date_pattern = r'^(\d{1,2})[./](\d{1,2})[./](\d{4})$'
        match = re.match(date_pattern, dob_text)
        
        if match:
            try:
                day, month, year = map(int, match.groups())
                birth_date = datetime(year, month, day)
                user_data['date_of_birth'] = dob_text
                
                # Calculate age
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                user_data['age'] = age
            except ValueError:
                await update.message.reply_text(
                    "Invalid date format. Please try again:\n"
                )
                return DATE_OF_BIRTH
        else:
            await update.message.reply_text(
                "Invalid date format. Please try again:\n"
            )
            return DATE_OF_BIRTH
        
        await update.message.reply_text(
            "Please specify your location (city, country)"
        )
        return LOCATION

    async def get_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store location and ask for medicine."""
        user_data = context.user_data
        user_data['location'] = update.message.text.strip()
        
        await update.message.reply_text(
            "What medications/drugs are you currently taking?\n\n"
            "Please specify name, dosage, and frequency\n\n"
            "If not taking any, write: 'Нет' or 'None'"
        )
        return MEDICINE

    async def get_medicine(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store medicine and ask for weight."""
        user_data = context.user_data
        user_data['medicine'] = update.message.text.strip()
        
        await update.message.reply_text(
            "Please specify your weight (in kilograms):\n\n"
        )
        return WEIGHT

    async def get_weight(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store weight and ask for height."""
        user_data = context.user_data
        weight_text = update.message.text.strip()
        
        try:
            weight = float(weight_text)
            if weight <= 0 or weight > 500:
                await update.message.reply_text(
                    "Please enter a realistic weight (1-500 kg)"
                )
                return WEIGHT
            user_data['weight'] = weight
        except ValueError:
            await update.message.reply_text(
                "Please enter weight as a number"
            )
            return WEIGHT
        
        await update.message.reply_text(
            "Please specify your height (in centimeters):\n\n"
        )
        return HEIGHT

    async def get_height(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store height and ask for complaints."""
        user_data = context.user_data
        height_text = update.message.text.strip()
        
        try:
            height = int(height_text)
            if height <= 0 or height > 250:
                await update.message.reply_text(
                    "Please enter a realistic height (1-250 cm)"
                )
                return HEIGHT
            user_data['height'] = height
            
            # Calculate BMI
            weight = user_data['weight']
            height_m = height / 100
            bmi = weight / (height_m ** 2)
            user_data['bmi'] = round(bmi, 1)
            
        except ValueError:
            await update.message.reply_text(
                "Please enter height as a number (in cm)"
            )
            return HEIGHT
        
        await update.message.reply_text(
            "Please describe your complaints and symptoms:\n\n"
            "Please be as detailed as possible"
        )
        return COMPLAINTS

    async def get_complaints(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store complaints and ask for medical history."""
        user_data = context.user_data
        user_data['complaints'] = update.message.text.strip()
        
        await update.message.reply_text(
            "Medical history (important facts from family history):\n\n"
            "Please specify:\n"
            "• Chronic diseases in family\n"
            "• Hereditary diseases\n"
            "• Important medical facts\n\n"
            "If none, write: 'No data'"
        )
        return MEDICAL_HISTORY

    async def get_medical_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store medical history and ask for test results."""
        user_data = context.user_data
        user_data['medical_history'] = update.message.text.strip()
        
        await update.message.reply_text(
            "Please attach test results"
        )
        return TEST_RESULTS

    async def get_test_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Excel file uploads and save them under data/{user_id}/{session_id}/test_results/."""
        document = update.message.document
        user_id = update.effective_user.id

        if document is None:
            await update.message.reply_text("❌ Please send an Excel file (.xlsx or .xls format).")
            return TEST_RESULTS

        # Check if the file is an Excel file
        if not document.file_name.lower().endswith(('.xlsx', '.xls')):
            await update.message.reply_text(
                "❌ Please send an Excel file (.xlsx or .xls format)."
            )
            return TEST_RESULTS  # Stay in same state

        try:
            # Get or set session ID
            session_id = context.user_data.get("session_id", 1)

            # Download file object from Telegram
            file = await context.bot.get_file(document.file_id)

            # Create structured directory
            directory_path = f"data/{user_id}/{session_id}/test_results"
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
            context.user_data["test_results_path"] = file_path

            # Confirm to user
            await update.message.reply_text(
                f"✅ Excel file saved successfully!\n\n"
                f"📄 *File name:* `{os.path.basename(file_path)}`\n"
                f"📁 *Saved to:* `{file_path}`",
                parse_mode="Markdown"
            )

            logger.info(f"Excel file saved: {file_path} for user {user_id}, session {session_id}")

            # Move to next step (e.g., DIAGNOSIS)
            await update.message.reply_text("🧬 Please enter your diagnosis:")
            return DIAGNOSIS

        except Exception as e:
            logger.error(f"Error saving Excel file: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error saving your Excel file. Please try again."
            )
            return TEST_RESULTS  # Stay in same state on failure
    
    async def invalid_test_result_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Please upload your test results as an Excel file (.xlsx or .xls).")
        return TEST_RESULTS
    
    async def get_diagnosis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store diagnosis and display all collected data."""
        user_data = context.user_data
        user_data['diagnosis'] = update.message.text.strip()
        
        # Calculate BMI category
        bmi = user_data.get('bmi', 0)
        if bmi < 18.5:
            bmi_category = "Недостаток веса / Underweight"
        elif bmi < 25:
            bmi_category = "Норма / Normal"
        elif bmi < 30:
            bmi_category = "Избыточный вес / Overweight"
        else:
            bmi_category = "Ожирение / Obesity"
        
        # Split data into multiple messages to avoid Telegram's character limit
        
        # Message 1: Header and basic info
        message1 = (
            "✅ 🏥 МЕДИЦИНСКАЯ КАРТА ПАЦИЕНТА\n"
            "PATIENT MEDICAL RECORD\n\n"
            f"👤 **Имя:** {user_data['name']}\n"
            f"⚧ **Пол:** {user_data['sex']}\n"
            f"📅 **Дата рождения:** {user_data['date_of_birth']} ({user_data['age']} лет)\n"
            f"📍 **Местоположение:** {user_data['location']}"
        )
        
        # Message 2: Physical data and medications
        message2 = (
            f"💊 **Лекарства:** {user_data['medicine']}\n"
            f"⚖️ **Вес:** {user_data['weight']} кг\n"
            f"📏 **Рост:** {user_data['height']} см\n"
            f"📊 **ИМТ:** {user_data['bmi']} ({bmi_category})"
        )
        
        # Message 3: Medical information (truncate if too long)
        complaints = user_data['complaints']
        if len(complaints) > 500:
            complaints = complaints[:500] + "..."
        
        medical_history = user_data['medical_history']
        if len(medical_history) > 500:
            medical_history = medical_history[:500] + "..."
        
        message3 = (
            f"🩺 **Жалобы:** {complaints}\n\n"
            f"📋 **Медицинская история:** {medical_history}"
        )
        
        # Message 4: Consultation and diagnosis
        diagnosis = user_data['diagnosis']
        if len(diagnosis) > 800:
            diagnosis = diagnosis[:800] + "..."
        
        message4 = (
            f"🔍 **Первичный диагноз:** {diagnosis}\n\n"
            "✅ Данные успешно собраны!\n\n"
            "🔄 /new - Новый пациент\n"
            "❓ /help - Помощь"
        )
        
        # Send messages sequentially
        try:
            await update.message.reply_text(message1, parse_mode='Markdown')
            await update.message.reply_text(message2, parse_mode='Markdown')
            await update.message.reply_text(message3, parse_mode='Markdown')
            await update.message.reply_text(message4, parse_mode='Markdown')
        except Exception as e:
            # Fallback: send without markdown if there are formatting issues
            await update.message.reply_text(message1)
            await update.message.reply_text(message2)
            await update.message.reply_text(message3)
            await update.message.reply_text(message4)
        
        # Log the collected data
        logger.info(f"Medical data collected for user {update.effective_user.id}: {user_data}")
        
        return ConversationHandler.END

    async def new_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start a new data collection session."""
        # Clear previous data
        context.user_data.clear()
        
        await update.message.reply_text(
            "🔄 Начинаем новую медицинскую консультацию!\n"
            "Starting a new medical consultation!\n\n"
            "1️⃣ Как вас зовут? (Полное имя)\n"
            "What's your full name?"
        )
        return NAME

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        await update.message.reply_text(
            "❌ Медицинская консультация отменена.\n"
            "Medical consultation cancelled.\n\n"
            "Команды / Commands:\n"
            "/start - Начать заново / Start again\n"
            "/help - Помощь / Help",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display help information."""
        help_text = (
            "🏥 **СИСТЕМА МЕДИЦИНСКОЙ КОНСУЛЬТАЦИИ**\n"
            "**MEDICAL CONSULTATION SYSTEM**\n\n"
            "**Доступные команды / Available commands:**\n"
            "• /start - Начать консультацию / Start consultation\n"
            "• /new - Новый пациент / New patient\n"
            "• /cancel - Отменить / Cancel current session\n"
            "• /help - Помощь / Help\n\n"
            "**Собираемая информация / Information collected:**\n"
            "1️⃣ Имя / Name\n"
            "2️⃣ Пол / Sex\n"
            "3️⃣ Дата рождения / Date of birth\n"
            "5️⃣ Местоположение / Location\n"
            "6️⃣ Лекарства / Medications\n"
            "7️⃣ Вес / Weight\n"
            "8️⃣ Рост / Height\n"
            "9️⃣ Жалобы пациента / Patient complaints\n"
            "🔟 Медицинская история / Medical history\n"
            "1️⃣1️⃣ Видеоконсультация / Videophone consultation\n"
            "1️⃣2️⃣ Первичный диагноз / Primary diagnosis\n\n"
            "После сбора всех данных можно начать новую консультацию!\n"
            "After collecting all data, you can start a new consultation!"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    def run(self):
        """Start the bot."""
        logger.info("Starting Medical Consultation Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

# Main execution
if __name__ == '__main__':
    bot = MedicalConsultationBot(BOT_TOKEN)
    bot.run()