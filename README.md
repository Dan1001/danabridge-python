# danabridge-python
Some python functions to use the unpublished danalock and danabridge api to lock/unlock and access/change pin codes. Intended to be incorporated into home automation code.

I'm not very good at this. The clever stuff reverse-engineering the api was done by @gechu, who has implemented an openapi and node-red flow here: https://github.com/gechu/unofficial-danalock-web-api

All I've done is translate into python functions, made it work if you have multiple danalocks, and done a teensy bit more probing so the functions can also read, change and delete PINs. I am horrible at coding so I'm sure this could be improved in a million ways. It does, however, seem to work.

None of this will work unless you have a danabridge, and the PIN stuff obviously only works if you also have a danapad.

But if you have all that, I reckon this ends up easier and faster than danalock's app or website. Dana make excellent and reliable hardware, but their app and website are slow and annoying, and they don't publish their API. 

Hopefully self-documented, more or less.

Have fun!
