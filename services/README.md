# TwitchTTSBot - Services

In order to start the TTS service and the bot you can use (in Linux) the `tts-web.service` and `tts.service`.

Remember to change the paths according to your system. In Ubuntu you should place the services in `/lib/systemd/system/`, and then run `sudo systemctl enable <service>.service`.