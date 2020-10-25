s = "<p,a,d>Hallo Welt"
t = ""
x = ""
if s.startswith("<"):
    for i in s:
        t += i
        if i == ">":
            break
print(t)
s = s[len(t):]
print(s)
