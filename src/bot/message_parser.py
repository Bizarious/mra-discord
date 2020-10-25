class MessageParser:

    class Context:

        def __init__(self):
            self.privacy = "private"
            self.message = ""

    def parse(self, msg: str, bot):
        ctx = self.Context()
        message = msg
        args = ""
        if message.startswith("<"):
            for s in message:
                args += s
                if s == ">":
                    break
        message = message[len(args):]
        args = (args[1:-1]).split(",")
        for a in args:
            if a == "p":
                ctx.privacy = "public"
            elif ":" in a:
                buffer = a.split(":")
                if buffer[0] == "m":
                    user = bot.get_user(int(buffer[1]))
                    message = user.mention + " " + message

        ctx.message = message
        return ctx


if __name__ == "__main__":
    m = MessageParser()
    m.parse("<p,s,c,m:Max>Hallo Welt", "")
