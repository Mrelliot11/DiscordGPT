import os
import openai
import discord
from dotenv import load_dotenv
from discord.ext import commands
from pathlib import Path

# Replace these with your Discord bot token and OpenAI API key
COMMAND_PREFIX = "!"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]


bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())

# Configure the OpenAI API
openai.api_key = OPENAI_API_KEY
# Rate limiting setup
cooldown = commands.CooldownMapping.from_cooldown(1, 30.0, commands.BucketType.user)

# Default parameters
params = {
    "temperature": 0.5,
    "model": "gpt-3.5-turbo",
    "max_tokens": 1024,
}

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.command(name="ask", help="Ask a question to the AI. Example: !ask What is the capital of France?")
async def ask(ctx, *, prompt: str = None):
    if not prompt:
        await ctx.send("Please provide a question.")
        return

    bucket = cooldown.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()

    if retry_after:
        await ctx.send(f"Please wait {retry_after:.1f} seconds before asking another question.")
        return

    response = openai.ChatCompletion.create(
        model=params["model"],
        messages=[{"role": "system", "content": "You are an AI that answers questions."},
                  {"role": "user", "content": prompt}],
        max_tokens=params["max_tokens"],
        n=1,
        temperature=params["temperature"],
    )

    answer = response.choices[0].message['content'].strip()
    await ctx.send(f"Answer: {answer}")


@bot.command(name="set_params", help="Set the temperature, model, and max_tokens parameters. Example: !set_params temperature=0.8 model=gpt-3.5-turbo max_tokens=1500")
async def set_params(ctx, *, args: str = None):
    if not args:
        await ctx.send("Please enter the parameters you want to set in the format 'key=value'. Available keys are: temperature, model, max_tokens.")
        return
    
    args_list = args.split()
    errors = []

    for arg in args_list:
        try:
            key, value = arg.split('=')

            if key == "temperature":
                temp = float(value)
                if 0.0 <= temp <= 1.0:
                    params["temperature"] = temp
                else:
                    errors.append("Temperature must be between 0.0 and 1.0.")

            elif key == "model":
                if value in ["gpt-3.5-turbo"]:  # Add other available models to the list if needed
                    params["model"] = value
                else:
                    errors.append(f"Invalid model '{value}'. Please choose a valid model.")

            elif key == "max_tokens":
                max_t = int(value)
                if 1 <= max_t <= 2048:
                    params["max_tokens"] = max_t
                else:
                    errors.append("Max tokens must be between 1 and 2048.")

        except ValueError:
            errors.append(f"Invalid input for '{arg}'. Please use the correct format.")
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")

    if errors:
        await ctx.send("\n".join(errors))
    else:
        await ctx.send(f"Parameters updated: temperature={params['temperature']}, model={params['model']}, max_tokens={params['max_tokens']}")

bot.run(DISCORD_BOT_TOKEN)
