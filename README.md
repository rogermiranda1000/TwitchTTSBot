# TwitchTTSBot
A Twitch bot that reads point redemptions with a custom trained voice.

Check the results on [my TTS gist](https://gist.github.com/rogermiranda1000/083eec93ebbdd1dcf8edea51cfc16bc5#examples).

## Run

Once you've done all the steps in [dependencies](#dependencies) you can run the bot.

To run the bot you'll have to first run (inside the `tts` conda environment) `cd rvc-tts-webui && python3 app.py`, and then (simultaneously) `cd TwitchTTSBot && python3 bot.py`. Check the README inside the `services` folder to auto-run those steps on every startup.

The bot will start the website [http://127.0.0.1:7890/?token=admin](http://127.0.0.1:7890/?token=admin) (or [https://127.0.0.1:7890/?token=admin](https://127.0.0.1:7890/?token=admin) if you have a secure certificate). The auth token can be changed in the config file; by default it is `admin`.

## Dependencies

#### Anaconda

- Install anaconda
- Create the conda environment: `conda create -n tts python=3.9`, and then activate it with `conda activate tts`
- Install pyTorch (if you want to use GPU): `conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia -y`

#### RVC-based TTS

##### Install

- Install `ffmpeg`
- Get the repo: `git clone https://github.com/litagin02/rvc-tts-webui.git && cd rvc-tts-webui`
- Download the models: `curl -L -O https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt ; curl -L -O https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt`
- Install the dependencies: `python3 -m pip install -r requirements.txt`
- Install some more dependencies so the bot can call it: `python3 -m pip install gradio-client==0.5.1`

If the install raises the error `Failed building wheel for pyworld`, run `python3 -m pip install numpy pyworld --no-build-isolation`

##### Get the model

- Train a RVC model
- Set the logs path (`<RVC path>/logs`) in the variable `model_root`, in `app.py`
- Copy the latest `.pth` file of the desired speaker from `<RVC path>/weights` into `<RVC path>/logs/<speaker>`

#### PythonTwitchBotFramework

##### Install

- Run `python3 -m pip install PythonTwitchBotFramework==2.11.5`
- For the bot dependencies, run `python3 -m pip install pypeln==0.4.9`

##### Creating the Twitch bot

- Create a Twitch account to be used as a bot
- [Create a new app](https://dev.twitch.tv/console/apps/create). Set a name, `Loyalty Tool` as category, and (if you don't want to use it) `http://localhost` as OAuth redirect
- In order to get the OAuth token have to enter the login link **(while being logged in in the bot account)**, and allow it. To generate the login link download `https://github.com/sharkbound/PythonTwitchBotFramework/blob/master/util/token_utils.py` and run `print(generate_irc_oauth('<app id>', 'http://localhost'))`. Once you allow it you'll be redirected to `localhost`; you'll have to copy the `access_token` GET param in the URL (that's the OAuth token).

Note: after some months the token will expire, and you'll have to re-run the last step and update the OAuth token.

##### Setting up the stream Twitch account

- While being logged in in the desired channel, allow the following link: `https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=<app id>&redirect_uri=http://localhost&scope=channel%3Aread%3Aredemptions`. Once you allow it you'll be redirected to `localhost`; you'll have to copy the `access_token` GET param in the URL (that's the PubSub token).
- Add a custom text reward redeem

##### Config setup

The first time you run the script it will raise a token exception, and it will generate some config files.

You'll have to edit `config.json`:

- Remove all commands in `command_whitelist`; leave only `"command_whitelist": []`
- Set the desired channel in `channels`
- Set the bot name in `nick` and `owner`
- Set the desired secret key in a new entry: `"secret": "admin"`. This will be needed for the audio player, as you'll have to enter to `localhost:7890?token=<secret>`
- Set the desired redeem name in a new entry: `"redeem": "Custom TTS"`
- Set the app id in `client_id`
- Set the OAuth token in `"oauth": "oauth:<token>"`
- Set the PubSub token in a new entry: `"pubsub": "<token>"`
- Set the `RVC-based TTS` model name in a new entry; you can also set for each model the Pitch shift in an `pitch-shift` entry:
```
"voices": {
    "<model name>": {
        "name": "<model name>",
        "voice": "en-US-AriaNeural-Female"
    }
}
```

Optional additional properties:

- You can add a character limit by setting `"input_limit": 450`
- You can add a segments limit by setting `"segments_limit": 12`. Note: one segment is one change of model, or a sound being played.
- To add sounds to be replaced you'll have to add an `audios` folder and place there the .wav; then create a new `audios` entry with each audio and :
```
"audios": {
    "[bruh]": { "files": [ "bruh.wav" ] },
    "[brah]": { "alias": "[bruh]" }
}
```

#### Website audio player

##### Install

- Run `python3 -m pip install Flask-SocketIO==4.3.1 python-engineio==3.13.2 python-socketio==4.6.0`

##### [Optional] Generating the SSL credentials

If you want to use this program securely (using https) with OBS you'll need a secure certificate. **Attention: in order to get a secure certificate you'll need a domain at your name, with an IP pointing to the server where you launch TwitchTTSBot. If you don't have such a thing, ignore this section and use the website with http.**

Follow the steps shown in [certbot instructions](https://certbot.eff.org/instructions?ws=other&os=ubuntufocal), and then renew it every few months with `sudo certbot renew --force-renewal`; you'll have to copy `privkey.pem` into `audio-server/key.pem`, and `cert.pem` into `audio-server/server.pem`.

Note: you may have to open port 80 on your router for the certbot certification.


## Run the tests

If you want to try the tests, start `app.py`, and inside TwitchTTSBot folder and with the `tts` environment enabled, run `python3 tests.py`
