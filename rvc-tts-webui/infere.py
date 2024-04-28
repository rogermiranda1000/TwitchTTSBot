#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import signal
import subprocess
from gradio_client import Client
from argparse import ArgumentParser
from time import sleep
from typing import List
from pydub import AudioSegment # generate empty audio if fails

def get_speakers() -> List[str]:
    return ['af-ZA-AdriNeural-Female', 'af-ZA-WillemNeural-Male', 'sq-AL-AnilaNeural-Female', 'sq-AL-IlirNeural-Male',
            'am-ET-AmehaNeural-Male', 'am-ET-MekdesNeural-Female', 'ar-DZ-AminaNeural-Female', 'ar-DZ-IsmaelNeural-Male',
            'ar-BH-AliNeural-Male', 'ar-BH-LailaNeural-Female', 'ar-EG-SalmaNeural-Female', 'ar-EG-ShakirNeural-Male',
            'ar-IQ-BasselNeural-Male', 'ar-IQ-RanaNeural-Female', 'ar-JO-SanaNeural-Female', 'ar-JO-TaimNeural-Male',
            'ar-KW-FahedNeural-Male', 'ar-KW-NouraNeural-Female', 'ar-LB-LaylaNeural-Female', 'ar-LB-RamiNeural-Male',
            'ar-LY-ImanNeural-Female', 'ar-LY-OmarNeural-Male', 'ar-MA-JamalNeural-Male', 'ar-MA-MounaNeural-Female',
            'ar-OM-AbdullahNeural-Male', 'ar-OM-AyshaNeural-Female', 'ar-QA-AmalNeural-Female', 'ar-QA-MoazNeural-Male',
            'ar-SA-HamedNeural-Male', 'ar-SA-ZariyahNeural-Female', 'ar-SY-AmanyNeural-Female', 'ar-SY-LaithNeural-Male',
            'ar-TN-HediNeural-Male', 'ar-TN-ReemNeural-Female', 'ar-AE-FatimaNeural-Female', 'ar-AE-HamdanNeural-Male',
            'ar-YE-MaryamNeural-Female', 'ar-YE-SalehNeural-Male', 'az-AZ-BabekNeural-Male', 'az-AZ-BanuNeural-Female',
            'bn-BD-NabanitaNeural-Female', 'bn-BD-PradeepNeural-Male', 'bn-IN-BashkarNeural-Male', 'bn-IN-TanishaaNeural-Female',
            'bs-BA-GoranNeural-Male', 'bs-BA-VesnaNeural-Female', 'bg-BG-BorislavNeural-Male', 'bg-BG-KalinaNeural-Female',
            'my-MM-NilarNeural-Female', 'my-MM-ThihaNeural-Male', 'ca-ES-EnricNeural-Male', 'ca-ES-JoanaNeural-Female',
            'zh-HK-HiuGaaiNeural-Female', 'zh-HK-HiuMaanNeural-Female', 'zh-HK-WanLungNeural-Male', 'zh-CN-XiaoxiaoNeural-Female',
            'zh-CN-XiaoyiNeural-Female', 'zh-CN-YunjianNeural-Male', 'zh-CN-YunxiNeural-Male', 'zh-CN-YunxiaNeural-Male',
            'zh-CN-YunyangNeural-Male', 'zh-CN-liaoning-XiaobeiNeural-Female', 'zh-TW-HsiaoChenNeural-Female', 'zh-TW-YunJheNeural-Male',
            'zh-TW-HsiaoYuNeural-Female', 'zh-CN-shaanxi-XiaoniNeural-Female', 'hr-HR-GabrijelaNeural-Female', 'hr-HR-SreckoNeural-Male',
            'cs-CZ-AntoninNeural-Male', 'cs-CZ-VlastaNeural-Female', 'da-DK-ChristelNeural-Female', 'da-DK-JeppeNeural-Male',
            'nl-BE-ArnaudNeural-Male', 'nl-BE-DenaNeural-Female', 'nl-NL-ColetteNeural-Female', 'nl-NL-FennaNeural-Female',
            'nl-NL-MaartenNeural-Male', 'en-AU-NatashaNeural-Female', 'en-AU-WilliamNeural-Male', 'en-CA-ClaraNeural-Female',
            'en-CA-LiamNeural-Male', 'en-HK-SamNeural-Male', 'en-HK-YanNeural-Female', 'en-IN-NeerjaExpressiveNeural-Female',
            'en-IN-NeerjaNeural-Female', 'en-IN-PrabhatNeural-Male', 'en-IE-ConnorNeural-Male', 'en-IE-EmilyNeural-Female',
            'en-KE-AsiliaNeural-Female', 'en-KE-ChilembaNeural-Male', 'en-NZ-MitchellNeural-Male', 'en-NZ-MollyNeural-Female',
            'en-NG-AbeoNeural-Male', 'en-NG-EzinneNeural-Female', 'en-PH-JamesNeural-Male', 'en-PH-RosaNeural-Female',
            'en-SG-LunaNeural-Female', 'en-SG-WayneNeural-Male', 'en-ZA-LeahNeural-Female', 'en-ZA-LukeNeural-Male',
            'en-TZ-ElimuNeural-Male', 'en-TZ-ImaniNeural-Female', 'en-GB-LibbyNeural-Female', 'en-GB-MaisieNeural-Female',
            'en-GB-RyanNeural-Male', 'en-GB-SoniaNeural-Female', 'en-GB-ThomasNeural-Male', 'en-US-AriaNeural-Female',
            'en-US-AnaNeural-Female', 'en-US-ChristopherNeural-Male', 'en-US-EricNeural-Male', 'en-US-GuyNeural-Male',
            'en-US-JennyNeural-Female', 'en-US-MichelleNeural-Female', 'en-US-RogerNeural-Male', 'en-US-SteffanNeural-Male',
            'et-EE-AnuNeural-Female', 'et-EE-KertNeural-Male', 'fil-PH-AngeloNeural-Male', 'fil-PH-BlessicaNeural-Female',
            'fi-FI-HarriNeural-Male', 'fi-FI-NooraNeural-Female', 'fr-BE-CharlineNeural-Female', 'fr-BE-GerardNeural-Male',
            'fr-CA-AntoineNeural-Male', 'fr-CA-JeanNeural-Male', 'fr-CA-SylvieNeural-Female', 'fr-FR-DeniseNeural-Female',
            'fr-FR-EloiseNeural-Female', 'fr-FR-HenriNeural-Male', 'fr-CH-ArianeNeural-Female', 'fr-CH-FabriceNeural-Male',
            'gl-ES-RoiNeural-Male', 'gl-ES-SabelaNeural-Female', 'ka-GE-EkaNeural-Female', 'ka-GE-GiorgiNeural-Male',
            'de-AT-IngridNeural-Female', 'de-AT-JonasNeural-Male', 'de-DE-AmalaNeural-Female', 'de-DE-ConradNeural-Male',
            'de-DE-KatjaNeural-Female', 'de-DE-KillianNeural-Male', 'de-CH-JanNeural-Male', 'de-CH-LeniNeural-Female',
            'el-GR-AthinaNeural-Female', 'el-GR-NestorasNeural-Male', 'gu-IN-DhwaniNeural-Female', 'gu-IN-NiranjanNeural-Male',
            'he-IL-AvriNeural-Male', 'he-IL-HilaNeural-Female', 'hi-IN-MadhurNeural-Male', 'hi-IN-SwaraNeural-Female',
            'hu-HU-NoemiNeural-Female', 'hu-HU-TamasNeural-Male', 'is-IS-GudrunNeural-Female', 'is-IS-GunnarNeural-Male',
            'id-ID-ArdiNeural-Male', 'id-ID-GadisNeural-Female', 'ga-IE-ColmNeural-Male', 'ga-IE-OrlaNeural-Female',
            'it-IT-DiegoNeural-Male', 'it-IT-ElsaNeural-Female', 'it-IT-IsabellaNeural-Female', 'ja-JP-KeitaNeural-Male',
            'ja-JP-NanamiNeural-Female', 'jv-ID-DimasNeural-Male', 'jv-ID-SitiNeural-Female', 'kn-IN-GaganNeural-Male',
            'kn-IN-SapnaNeural-Female', 'kk-KZ-AigulNeural-Female', 'kk-KZ-DauletNeural-Male', 'km-KH-PisethNeural-Male',
            'km-KH-SreymomNeural-Female', 'ko-KR-InJoonNeural-Male', 'ko-KR-SunHiNeural-Female', 'lo-LA-ChanthavongNeural-Male',
            'lo-LA-KeomanyNeural-Female', 'lv-LV-EveritaNeural-Female', 'lv-LV-NilsNeural-Male', 'lt-LT-LeonasNeural-Male',
            'lt-LT-OnaNeural-Female', 'mk-MK-AleksandarNeural-Male', 'mk-MK-MarijaNeural-Female', 'ms-MY-OsmanNeural-Male',
            'ms-MY-YasminNeural-Female', 'ml-IN-MidhunNeural-Male', 'ml-IN-SobhanaNeural-Female', 'mt-MT-GraceNeural-Female',
            'mt-MT-JosephNeural-Male', 'mr-IN-AarohiNeural-Female', 'mr-IN-ManoharNeural-Male', 'mn-MN-BataaNeural-Male',
            'mn-MN-YesuiNeural-Female', 'ne-NP-HemkalaNeural-Female', 'ne-NP-SagarNeural-Male', 'nb-NO-FinnNeural-Male',
            'nb-NO-PernilleNeural-Female', 'ps-AF-GulNawazNeural-Male', 'ps-AF-LatifaNeural-Female', 'fa-IR-DilaraNeural-Female',
            'fa-IR-FaridNeural-Male', 'pl-PL-MarekNeural-Male', 'pl-PL-ZofiaNeural-Female', 'pt-BR-AntonioNeural-Male',
            'pt-BR-FranciscaNeural-Female', 'pt-PT-DuarteNeural-Male', 'pt-PT-RaquelNeural-Female', 'ro-RO-AlinaNeural-Female',
            'ro-RO-EmilNeural-Male', 'ru-RU-DmitryNeural-Male', 'ru-RU-SvetlanaNeural-Female', 'sr-RS-NicholasNeural-Male',
            'sr-RS-SophieNeural-Female', 'si-LK-SameeraNeural-Male', 'si-LK-ThiliniNeural-Female', 'sk-SK-LukasNeural-Male',
            'sk-SK-ViktoriaNeural-Female', 'sl-SI-PetraNeural-Female', 'sl-SI-RokNeural-Male', 'so-SO-MuuseNeural-Male',
            'so-SO-UbaxNeural-Female', 'es-AR-ElenaNeural-Female', 'es-AR-TomasNeural-Male', 'es-BO-MarceloNeural-Male',
            'es-BO-SofiaNeural-Female', 'es-CL-CatalinaNeural-Female', 'es-CL-LorenzoNeural-Male', 'es-CO-GonzaloNeural-Male',
            'es-CO-SalomeNeural-Female', 'es-CR-JuanNeural-Male', 'es-CR-MariaNeural-Female', 'es-CU-BelkysNeural-Female',
            'es-CU-ManuelNeural-Male', 'es-DO-EmilioNeural-Male', 'es-DO-RamonaNeural-Female', 'es-EC-AndreaNeural-Female',
            'es-EC-LuisNeural-Male', 'es-SV-LorenaNeural-Female', 'es-SV-RodrigoNeural-Male', 'es-GQ-JavierNeural-Male',
            'es-GQ-TeresaNeural-Female', 'es-GT-AndresNeural-Male', 'es-GT-MartaNeural-Female', 'es-HN-CarlosNeural-Male',
            'es-HN-KarlaNeural-Female', 'es-MX-DaliaNeural-Female', 'es-MX-JorgeNeural-Male', 'es-NI-FedericoNeural-Male',
            'es-NI-YolandaNeural-Female', 'es-PA-MargaritaNeural-Female', 'es-PA-RobertoNeural-Male', 'es-PY-MarioNeural-Male',
            'es-PY-TaniaNeural-Female', 'es-PE-AlexNeural-Male', 'es-PE-CamilaNeural-Female', 'es-PR-KarinaNeural-Female',
            'es-PR-VictorNeural-Male', 'es-ES-AlvaroNeural-Male', 'es-ES-ElviraNeural-Female', 'es-US-AlonsoNeural-Male',
            'es-US-PalomaNeural-Female', 'es-UY-MateoNeural-Male', 'es-UY-ValentinaNeural-Female', 'es-VE-PaolaNeural-Female',
            'es-VE-SebastianNeural-Male', 'su-ID-JajangNeural-Male', 'su-ID-TutiNeural-Female', 'sw-KE-RafikiNeural-Male',
            'sw-KE-ZuriNeural-Female', 'sw-TZ-DaudiNeural-Male', 'sw-TZ-RehemaNeural-Female', 'sv-SE-MattiasNeural-Male',
            'sv-SE-SofieNeural-Female', 'ta-IN-PallaviNeural-Female', 'ta-IN-ValluvarNeural-Male', 'ta-MY-KaniNeural-Female',
            'ta-MY-SuryaNeural-Male', 'ta-SG-AnbuNeural-Male', 'ta-SG-VenbaNeural-Female', 'ta-LK-KumarNeural-Male',
            'ta-LK-SaranyaNeural-Female', 'te-IN-MohanNeural-Male', 'te-IN-ShrutiNeural-Female', 'th-TH-NiwatNeural-Male',
            'th-TH-PremwadeeNeural-Female', 'tr-TR-AhmetNeural-Male', 'tr-TR-EmelNeural-Female', 'uk-UA-OstapNeural-Male',
            'uk-UA-PolinaNeural-Female', 'ur-IN-GulNeural-Female', 'ur-IN-SalmanNeural-Male', 'ur-PK-AsadNeural-Male',
            'ur-PK-UzmaNeural-Female', 'uz-UZ-MadinaNeural-Female', 'uz-UZ-SardorNeural-Male', 'vi-VN-HoaiMyNeural-Female',
            'vi-VN-NamMinhNeural-Male', 'cy-GB-AledNeural-Male', 'cy-GB-NiaNeural-Female', 'zu-ZA-ThandoNeural-Female', 'zu-ZA-ThembaNeural-Male']

def infere(model: str, text: str, out: str, speed: int = 0, transpose: int = 0, speaker: str = 'en-US-AriaNeural-Female'):
    """
    Run TTS.
    :param model:       Model name (folder name inside `weights`)
    :param text:        Text to infere
    :param out:         Where to place the result
    :param speed:       Talk speed (from -100 to 100)
    :param transpose:   Pitch note shift
    :param speaker:     Base speaker to infere the TTS (check `get_speakers()` list)
    """
    client = Client("http://127.0.0.1:7860/")
    print(f"[v] Synthesizing '{text}'...")
    result = client.predict(model,
                    speed,
                    text,
                    speaker,
                    transpose,
                    "rmvpe",
                    1,	# int | float (numeric value between 0 and 1) in 'Index rate' Slider component
                    0.33,	# int | float (numeric value between 0 and 0.5) in 'Protect' Slider component
                    fn_index=0
    )

    audio = result[-1]
    try:
        print(f"[v] Done synthesizing (result on {audio}); copying file into {out}...")
        shutil.move(audio, out)
    except Exception as ex:
        print(f"[w] An exception has occurred while trying to synthetize TTS; generating an empty audio...")
        AudioSegment.silent(duration=10).export(out_f = out, format = "wav")

def main():
    argParser = ArgumentParser()
    argParser.add_argument("-m", "--model", required=True)
    argParser.add_argument("-t", "--text", required=True)
    argParser.add_argument("-sp", "--speed", type=int, default=0)
    argParser.add_argument("-tr", "--transpose", type=int, default=0)
    argParser.add_argument("-o", "--out", default='out.wav')
    argParser.add_argument("-v", "--voice", default='en-US-AriaNeural-Female')

    args = argParser.parse_args()

    infere(args.model, args.text, args.out, speed=args.speed, transpose=args.transpose, speaker=args.voice)

if __name__ == '__main__':
    main()
