import requests
import discord
import time
from datetime import datetime as dt, timedelta as td
from discord.ext import commands
from core.database import ConfigManager
from core.enums import Dates
from core.permissions import is_owner, is_group_member


def get_current_weather(city: str, token: str) -> dict:
    response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={token}&units=metric")
    return response.json()


def get_forecast(city: str, token: str) -> dict:
    response = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={token}&units=metric")
    return response.json()


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.permit.add_group("weather", True)
        self.config: ConfigManager = self.bot.config
        self.token: str = self.config.get_token("weather")
        if self.token is None:
            raise RuntimeError("You need to assign a weather token")

        self.current_weather = {}   # city -> [current weather as dict, date]
        self.forecast_weather = {}  # city -> [forecast weather as dict, date]

    def get_weather_data(self, mode: str, city: str) -> list:
        if mode == "current":
            if city not in self.current_weather.keys():
                self.current_weather[city] = [get_current_weather(city, self.token), time.time()]
            else:
                now = time.time()
                if now > self.current_weather[city][1] + 60:
                    self.current_weather[city] = [get_current_weather(city, self.token), time.time()]
            return self.current_weather[city]

        elif mode == "forecast":
            if city not in self.forecast_weather.keys():
                self.forecast_weather[city] = [get_forecast(city, self.token), time.time()]
            else:
                now = time.time()
                if now > self.forecast_weather[city][1] + 900:
                    self.forecast_weather[city] = [get_forecast(city, self.token), time.time()]
            return self.forecast_weather[city]

        else:
            raise RuntimeError(f"'{mode}' is no valid argument")

    @commands.cooldown(rate=1, per=5)
    @commands.command()
    @commands.check_any(commands.check(is_owner),
                        commands.check(is_group_member("weather")))
    async def weather(self, ctx, city):
        """
        Displays the current weather in a city.
        """
        data_list: list = self.get_weather_data("current", city)
        data: dict = data_list[0]

        if data["cod"] == 404:
            raise RuntimeError("Error in api call")
        elif data["cod"] == 401:
            raise RuntimeError("Invalid API Key")

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

    @commands.cooldown(rate=1, per=5)
    @commands.command()
    @commands.check_any(commands.check(is_owner),
                        commands.check(is_group_member("weather")))
    async def forecast(self, ctx, city, day="today", detail="less"):
        """
        Displays the weather forecast for a city.

        day:

            The day, of which the forecast shall be displayed.
            Options:

                today
                tomorrow
                specific day (e.g. 01.01.21)

        detail:

            The detail of the displayed data.
            less:

                Only max, min temperature and rain

            complete:

                complete data, every 3 hours
        """
        if day == "today":
            date = dt.now().date()
        elif day == "tomorrow":
            date = dt.now().date() + td(days=1)
        else:
            date = dt.strptime(day, Dates.DATE_FORMAT_DATE_ONLY.value).date()

        utc_offset = dt.now() - dt.utcnow()

        data_list: list = self.get_weather_data("forecast", city)
        data: dict = data_list[0]

        if data["cod"] == 404:
            raise RuntimeError("Error in api call")
        elif data["cod"] == 401:
            raise RuntimeError("Invalid API Key")

        update_time: str = dt.fromtimestamp(data_list[1]).strftime(Dates.DATE_FORMAT.value)
        weather_list: list = data["list"]
        timezone = td(seconds=data["city"]["timezone"])

        weather_data = []
        for i in weather_list:
            d = ((dt.fromtimestamp(i["dt"]) - utc_offset) + timezone).date()
            if d == date:
                weather_data.append(i)

        e = discord.Embed(title=f"Weather in {city}, {date.strftime(Dates.DATE_FORMAT_DATE_ONLY.value)}",
                          color=discord.Colour.blue()
                          )
        if not weather_data:
            e.add_field(name="No data available", value="There is no data available for this day.")

        if detail == "complete":
            for i in weather_data:
                d = ((dt.fromtimestamp(i["dt"]) - utc_offset) + timezone).strftime(Dates.TIME_FORMAT.value)
                description = i["weather"][0]["description"]
                temp = i["main"]["temp"]
                if "rain" in i.keys():
                    rain = i["rain"]["3h"]
                else:
                    rain = 0

                e.add_field(name=d, value=f"{description}\n{temp}°C\n{rain} mm", inline=True)

        else:
            temps = []
            rain = []
            for i in weather_data:
                temps.append(i["main"]["temp"])
                if "rain" in i.keys():
                    rain.append(i["rain"]["3h"])
                else:
                    rain.append(0)
            max_temp = max(temps)
            min_temp = min(temps)
            max_rain = max(rain)

            e.add_field(name="Max Temperature", value=f"{max_temp}°C", inline=True)
            e.add_field(name="Min Temperature", value=f"{min_temp}°C", inline=True)
            e.add_field(name="Max Rain", value=f"{max_rain} mm", inline=False)

        e.set_footer(text=f"Last updated: {update_time}")

        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Weather(bot))
