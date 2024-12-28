import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from rembg import remove
from PIL import Image, ImageDraw, ImageFont
import io
import asyncio
from aiohttp import web

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7909357054:AAFLkukILIKpCWegQi1hUUxcUgkSQti2OlU"

TEMPLATE_PATHS = {
    "India": {
        "normal": "templates/india_template.jpg",
        "special": "templates/india_Special_template.jpg"
    },
    "New Zealand": {
        "normal": "templates/newzealand_template.jpg",
        "special": "templates/england_Special_template.png"
    },
    "Australia": {
        "normal": "templates/australia_template.jpg",
        "special": "templates/australia_Special_template.png"
    }
}

PLAYER_IMAGE_SIZE = (850, 660)
NAME_POSITION = (430, 700)
BAT_RATING_POSITION = (200, 920)
BOWL_RATING_POSITION = (530, 920)

DETAILS_KEY = "details"
PLAYER_IMAGE_KEY = "player_image"
SELECTED_COUNTRY_KEY = "selected_country"

# Folder where the cricket cards will be saved
CARDS_FOLDER = "new_cards"

# Create the new_cards folder if it doesn't exist
if not os.path.exists(CARDS_FOLDER):
    os.makedirs(CARDS_FOLDER)

# Function to draw centered text
def draw_centered_text(draw, text, font, y_position, template_width, x_offset):
    text_bbox = font.getbbox(text)
    text_width = text_bbox[2] - text_bbox[0]
    x_position = x_offset - text_width // 2
    draw.text((x_position, y_position), text, font=font, fill=(255, 255, 255, 255))

async def handle_photo(update: Update, context: CallbackContext):
    if not update.message.photo:
        await update.message.reply_text("Please send a valid player photo.")
        return

    photo = update.message.photo[-1]
    try:
        image_file = await photo.get_file()
        image_bytes = await image_file.download_as_bytearray()
        player_image = remove(image_bytes, force_return_bytes=True)
        context.user_data[PLAYER_IMAGE_KEY] = player_image
        logger.info("Player image downloaded and background removed.")
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("Error processing the image. Please try again.")
        return

    caption = update.message.caption or ""
    try:
        details = extract_player_details(caption)
        context.user_data[DETAILS_KEY] = details
        logger.info(f"Extracted player details: {details}")

        keyboard = [
            [InlineKeyboardButton(country, callback_data=country)] for country in TEMPLATE_PATHS.keys()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Which country's template should I use?", reply_markup=reply_markup
        )
    except ValueError as e:
        logger.error(f"Error extracting details: {e}")
        await update.message.reply_text(f"Error: {e}")

async def handle_country_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    country = query.data
    context.user_data[SELECTED_COUNTRY_KEY] = country

    keyboard = [
        [InlineKeyboardButton("Normal", callback_data=f"{country}_normal")],
        [InlineKeyboardButton("Special", callback_data=f"{country}_special")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(
        text=f"Select template type for {country}:",
        reply_markup=reply_markup
    )

async def handle_template_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_option = query.data.split("_")
    country = selected_option[0]
    template_type = selected_option[1]

    if country not in TEMPLATE_PATHS or template_type not in TEMPLATE_PATHS[country]:
        await query.answer()
        await query.edit_message_text(text="Invalid selection, please try again.")
        return

    template_path = TEMPLATE_PATHS[country][template_type]
    details = context.user_data.get(DETAILS_KEY)
    player_image_bytes = context.user_data.get(PLAYER_IMAGE_KEY)

    if not details or not player_image_bytes:
        await query.answer()
        await query.edit_message_text("Missing player details or photo. Please restart the process.")
        return

    try:
        # Create the card using the selected template
        card_template = Image.open(template_path).convert("RGBA")
        template_width, template_height = card_template.size
        player_image = Image.open(io.BytesIO(player_image_bytes)).convert("RGBA")
        left, top, right, bottom = 200, 170, 930, 660
        target_width = right - left
        target_height = bottom - top
        player_image = player_image.resize((target_width, target_height), Image.LANCZOS)
        card_template.paste(player_image, (left, top), player_image)
        draw = ImageDraw.Draw(card_template)
        font = ImageFont.truetype("arial.ttf", size=70)
        bold_font = ImageFont.truetype("arialbd.ttf", size=70)

        # Name text positioning
        name_text = details["name"]
        name_bbox = font.getbbox(name_text)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (template_width - name_width) // 2
        draw.text((name_x, NAME_POSITION[1]), name_text, font=font, fill=(255, 255, 255, 255))

        # Draw BAT and BOWL ratings with dynamic centering
        draw_centered_text(
            draw,
            f"         {details['bat_rating']}",
            bold_font,
            BAT_RATING_POSITION[1],
            template_width,
            BAT_RATING_POSITION[0]
        )

        draw_centered_text(
            draw,  
            f"        {details['bowl_rating']}",
            bold_font,
            BOWL_RATING_POSITION[1],
            template_width,
            BOWL_RATING_POSITION[0]
        )

        # Save the card to the PC
        player_name = details["name"].replace(" ", "_")
        output_path = os.path.join(CARDS_FOLDER, f"{player_name}.png")
        card_template.save(output_path, format="PNG")
        logger.info(f"Cricket card saved to {output_path}")

        # Send the card back to the user
        output_image = io.BytesIO()
        card_template.save(output_image, format="PNG")
        output_image.seek(0)
        await query.answer()
        await query.edit_message_text(text="Creating your cricket card...")
        await query.message.reply_photo(
            photo=output_image, caption="Here is your cricket card!"
        )
        logger.info("Cricket card sent successfully.")
    except Exception as e:
        logger.error(f"Error creating card: {e}")
        await query.answer()
        await query.edit_message_text("An error occurred while creating the card.")

def extract_player_details(caption: str):
    details = {"name": "", "bat_rating": "0", "bowl_rating": "0"}
    lines = [line.strip() for line in caption.strip().split("\n") if line.strip()]
    if len(lines) < 3:
        raise ValueError(
            "Please provide details in the format:\n\n"
            "Name\nBAT RATING:- X\nBOWL RATING:- X"
        )
    details["name"] = lines[0]
    for line in lines[1:]:
        if "BAT RATING" in line.upper():
            details["bat_rating"] = line.split(":", 1)[-1].replace("-", "").strip()
        elif "BOWL RATING" in line.upper():
            details["bowl_rating"] = line.split(":", 1)[-1].replace("-", "").strip()
    if not details["bat_rating"].isdigit() or not details["bowl_rating"].isdigit():
        raise ValueError(
            "Invalid rating format. Ratings should be numeric, e.g., BAT RATING:- 69."
        )
    return details

async def health_check(request):
    """Health check endpoint."""
    return web.Response(text="OK", status=200)

async def start_health_server():
    """Starts a lightweight HTTP server for health checks."""
    app = web.Application()
    app.add_routes([web.get("/", health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    logger.info("Health check server running on port 8000")

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT, handle_country_selection))
    application.add_handler(CallbackQueryHandler(handle_country_selection, pattern="^(India|New Zealand|Australia)$"))
    application.add_handler(CallbackQueryHandler(handle_template_selection, pattern="^(India|New Zealand|Australia)_(normal|special)$"))

    # Start health check server and bot polling concurrently
    await asyncio.gather(
        start_health_server(),
        application.run_polling()
    )

if __name__ == "__main__":
    asyncio.run(main())
