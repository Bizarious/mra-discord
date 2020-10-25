try:
    raise RuntimeError("Testing")
except RuntimeError as e:
    print(isinstance(e, Exception))
    raise e
