import requests
import discord
import time
from datetime import datetime as dt
from discord.ext import commands
from core.database import ConfigManager
from core.enums import Dates
from core.permissions import is_owner, is_group_member


def get_current_weather(city: str, token: str) -> dict:
    response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={token}&units=metric")
    r = response.json()
    if r["cod"] == "404":
        raise RuntimeError("Error in api call")
    return r


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.permit.add_group("weather", True)
        self.config: ConfigManager = self.bot.config
        self.token: str = self.config.get_token("weather")
        if self.token is None:
            raise RuntimeError("You need to assign a weather token")

        self.current_weather = {}   # city -> [current weather as dict, date]

    def get_weather_data(self, mode, city: str) -> list:
        if mode == "current":
            if city not in self.current_weather.keys():
                self.current_weather[city] = [get_current_weather(city, self.token), time.time()]
            else:
                now = time.time()
                if now > self.current_weather[city][1] + 60:
                    self.current_weather[city] = [get_current_weather(city, self.token), time.time()]
            return self.current_weather[city]
        else:
            raise RuntimeError(f"'{mode}' is no valid argument")

    @commands.cooldown(rate=1, per=5)
    @commands.command()
    @commands.check_any(commands.check(is_owner),
                        commands.check(is_group_member("weather")))
    async def weather(self, ctx, city):
        data_list: list = self.get_weather_data("current", city)
        data: dict = data_list[0]
        update_time = dt.fromtimestamp(data_list[1]).strftime(Dates.DATE_FORMAT.value)
        wth = data["weather"]
        main = data["main"]
        wind = data["wind"]

        description = wth[0]["description"]
        temp = main["temp"]
        wind_speed = wind["speed"]
        pressure = main["pressure"]
        humidity = main["humidity"]

        e = discord.Embed(title=f"Current weather in {city}",
                          color=discord.Colour.blue()
                          )
        e.add_field(name="Description", value=description, inline=False)
        e.add_field(name="Temperature", value=f"{temp}°C", inline=False)
        e.add_field(name="Wind", value=f"{wind_speed} km/h", inline=True)
        e.add_field(name="Pressure", value=f"{pressure} hPa", inline=True)
        e.add_field(name="Humidity", value=f"{humidity}%", inline=True)
        e.set_footer(text=f"Last updated: {update_time}")

        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Weather(bot))
