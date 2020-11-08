class MessageParser:

    class Context:

        def __init__(self):
            self.privacy = "private"
            self.message = ""

    def parse(self, msg: str, msg_args: str) -> Context:
        ctx = self.Context()
        message = msg
        msg_args = msg_args.split(",")

        for s in msg_args:
            if s == "p":
                ctx.privacy = "public"
            elif s.startswith("m:"):
                s = s.split(":")
                message = f"<@{s[1]}> {message}"

        ctx.message = message
        return ctx


if __name__ == "__main__":
    m = MessageParser()
    m.parse("Hallo Welt", "p,s,c,m:123")
