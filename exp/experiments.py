def dec(fct):
    fct()


@dec
def hello():    # dec(hello)
    print("Hello World")


def dec2(x):
    def sub_dec(fct):
        fct(x)
    return sub_dec


@dec2("Moin")
def hello2(x):  # dec2("Moin")(hello2) -> sub_dec(hello)
    print(x)
