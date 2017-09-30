# IEDLCDEditor
Infinity ErgoDox LCD Editor, by LuX
Permission to post in [GeekHack thread](https://geekhack.org/index.php?topic=82904.msg2213564#msg2213564)

-----
## Original Text of Posting
-----
From [GeekHack thread](https://geekhack.org/index.php?topic=82904.msg2201059#msg2201059)

After getting my ergodox infinity I wasn't that excited with the default images and colors on the LCD screen. I realized modding them by directly manipulating the flashing files was really easy and doesn't require special compilers and such... I also saw people asking for such a software, so I made a quick and simple program that does just that, but after a day and zero downloads from [I:C forums](https://input.club/forums/topic/ied-lcd-editor-v0-9-gui-editor-to-modify-the-lcd) it's obvious no one will find it there, so I'll post about it here as well. Hopefully someone will find it useful.

-----
## Requirements
-----
The application is written in Python 3 and requires some additional libraries to run properly. These can be installed using _pip_ or your preferred package manager.

- pytk
- Pillow
- easygui
- pyserial

If you are using _pip_ these dependencies can be installed using the supplied requirements file, by running: `pip install -r requirements.txt`

-----
## Instructions for Use
-----
Next you need the .dfu.bin files from the configurator: https://input.club/configurator-ergodox and drop them in the folder.

The application has been tested on Windows and Linux (Ubuntu) but theoretically it should be cross-platform. If something doesn't work I can try to fix it, or upload the source so someone on a different platform can try and port it or add functionality.

Some images:
As you can see I've put Func4 to be backlights off, this way I can easily turn off the lights during the night.
Ironically I haven't yet figured out how to change the default layer led color directly, which was what I originally wanted to do, so you'll be stuck with the default. Everything else works.

![LCD Editor Image](http://i.imgur.com/SyuoqQa.png)

-----
## License
-----
This code and all files included are licensed under MS-PL, included in the archive.
