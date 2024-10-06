# Description: This script converts a pdf file to a podcast using Azure OpenAI GPT-4-O and Azure TTS
import os

# setuop your AOAI endpoint, key and speech resource etc.
AOAI_KEY = os.getenv("AO_KEY")
AOAI_ENDPOINT = os.getenv("AURI")
AOAI_MODEL_NAME = "gpt-4o"
AOAI_MODEL_VERSION = "2024-02-15-preview"

speech_key = os.getenv("TTSKEY")
service_region = os.getenv("TTSLOC")

FIRECRAWL_KEY = os.getenv("FC_KEY")


def printwithtime(*args):
    # show milliseconds
    import datetime
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), *args)

# extract ssml from website
def CreatePodcastSsml(text):
    # call Azure OpenAI GPT-4
    import os
    from openai import AzureOpenAI

    client = AzureOpenAI(
        api_key = AOAI_KEY,  
        api_version = AOAI_MODEL_VERSION,
        azure_endpoint = AOAI_ENDPOINT
        )

    prompt =  """
        Create a conversational, engaging podcast script named 'Charlies News Podcast' between two hosts from the input text. Use informal language like haha, wow etc. and keep it engaging.
        Think step by step, grasp the key points of the paper, and explain them in a conversational tone, at the end, summarize. 
        Output into SSML format like below, please don't change voice name
	    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='en-EN'>
	    <voice name='en-us-emma2:DragonHDLatestNeural'>text</voice> 
        <voice name='en-US-Andrew:DragonHDLatestNeural'>text</voice>
        </speak>
        """
    podcasttext = ""
    trycount = 3
    while trycount > 0:
        try:
            completion = client.chat.completions.create(
                model=AOAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None)
            
            podcasttext = completion.choices[0].message.content 
            break
        except Exception as e:
            print(e)
            trycount -= 1
            continue

    # create ssml
    return podcasttext 

# generate audio with Azure TTS HD voices
def GenerateAudio(ssml, outaudio):
    import azure.cognitiveservices.speech as speechsdk
    import os
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    # Creates an audio configuration that points to an audio file.
    audio_output = speechsdk.audio.AudioOutputConfig(filename=outaudio)

    # Creates a speech synthesizer using the Azure Speech Service.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)

    # Synthesizes the received text to speech.
    result = speech_synthesizer.speak_ssml_async(ssml).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesis was successful. Audio was written to '{}'".format(outaudio))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
        print("Did you update the subscription info?")

# generate pod cast workflow
def GeneratePodcast(url, outaudio, coverimage = None):  
    from firecrawl import FirecrawlApp

    printwithtime("Generating podcast from website: ", url)


    printwithtime("Extracting text from url as MD")
    app = FirecrawlApp(api_key=FIRECRAWL_KEY)

    # Scrape a website:
    scrape_status = app.scrape_url(url, params={'formats': ['markdown']})

    text = scrape_status['markdown']
    print ("Text: ", text)


    # create podcast ssml
    printwithtime("Creating podcast ssml")
    ssml = CreatePodcastSsml(text)
    print(ssml)
    
    # generate podcast
    printwithtime("Generating podcast with Azure TTS")
    GenerateAudio(ssml, outaudio)

# helper
def GeneratePodcastFromUrl(url, outaudio = None):
    # get the file name from url
    if outaudio is None:
        outaudio  = url.rstrip('/').split('/')[-1] + ".wav"
    GeneratePodcast(url, outaudio)

# main func
if __name__ == "__main__":
    GeneratePodcastFromUrl("https://ai.meta.com/blog/movie-gen-media-foundation-models-generative-ai-video/")
   