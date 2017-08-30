import qi
import threading
import random
import csv

class EmotionRobot(object):
	def __init__(self, session):
		self.PACKAGE_UUID = "EmotionProject" #Package ID of the Choregraph project
		self.session = session
		self.module_name = "GingerEmotion"
		self.valence = 0.0
		self.arousal = 0.0
		self.extraversion = 0.7
		
		self.emotion = ["calm", 1]		
		self.emotions = ["angry", "sad", "excited", "happy", "calm"]
		self.activation_levels = [0.0, 0.0, 0.0, 0.0, 0.0]
		self.elicitor_levels = [0.0, 0.0, 0.0, 0.0, 0.0]
		self.thresholds = [[-0.5, 0.5], [-0.5, -0.5], [0.25, 0.75], [0.75, 0.25], [0.25, -0.25]]
		self.decay_levels = [0.0, 0.0, 0.0, 0.0, 0.0]
		self.desirability = [-1.0, -0.5, 0.0, 1.0, 0.0]
		
		self.default_volume = self.tts().getVolume()
		
		self.face_valence = 0.0
		self.face_arousal = 0.0
		self.voice_valence = 0.0
		self.voice_arousal = 0.0
		self.occurrence = 0.0
		
		self.file_writer = csv.writer(open('test.csv', 'wb'), delimiter=',')
		
	def start(self):
		self.subscribingLock = threading.Lock()
		self.setALMemorySubscription(True)
		print self.module_name, "service started..."
	
	def stop(self):
		self.stop_resetchat()
		self.setALMemorySubscription(False)
		
	def mem(self):
		return self.session.service("ALMemory")
	
	def leds(self):
		return self.session.service("ALLeds")
		
	def tts(self):
		return self.session.service("ALTextToSpeech")
		
	def ms(self):
		return self.session.service("ALMotion")
		
	def ps(self):
		return self.session.service("ALRobotPosture")
		
	def ALDialog(self):
		return self.session.service("ALDialog")
		
	def ALVoiceEmotion(self):
		return self.session.service("ALVoiceEmotionAnalysis")
	
	def calculate_valence_robot(self, valence_user):
		valence_old = self.valence
		# if valence_user is not None:
			# # valence_user = self.mem().getData("Ginger/UserValence")
			# valence_new = valence_old + ((valence_user+self.occurrence)/2 - valence_old)/2
			# self.valence = valence_new
			# return valence_new
		# else:
			# valence_new = valence_old + (self.occurrence - valence_old)/2
			# self.valence = valence_new
			# return valence_new
			
		valence_new = valence_old + ((valence_user+self.occurrence)/2.0 - valence_old)/2.0
		self.valence = valence_new
		print 'valence new = ' + str(valence_new)
		return valence_new
	
	def calculate_arousal_robot(self, arousal_user):
		arousal_old = self.arousal
		# if arousal_user is not None:
			# #arousal_user = self.mem().getData("Ginger/UserArousal")
			# arousal_new = arousal_old + ((arousal_user+self.occurrence)/2 - arousal_old)/2
			# self.arousal = arousal_new
			# return arousal_new
		# else:
			# #arousal_user = self.mem().getData("Ginger/UserArousal")
			# arousal_new = arousal_old + (self.occurrence - arousal_old)/2
			# self.arousal = arousal_new
			# return arousal_new
		
		arousal_new = arousal_old + ((arousal_user+self.occurrence)/2 - arousal_old)/2
		self.arousal = arousal_new
		return arousal_new
		
	def calculate_activate_emotion(self):
		valence = self.valence
		arousal = self.arousal
		
		activated_value = 0.0
		activated_emotion = self.emotion[0]
		i = 0
		for emotion in self.emotions:
			thresholds = self.thresholds[i]
			difference = ((thresholds[0]-valence)**2 + (thresholds[1]-arousal)**2)**0.5
			if difference <= 0.25:
				self.elicitor_levels[i] = 1.0
			else:
				self.elicitor_levels[i] = -((difference-(8.0**0.5))/((8.0**0.5)-0.25)) #between 0 and 1
		
			decay = self.decay_levels[i]
			desirability = self.desirability[i]
			activation_level = 0.75*self.elicitor_levels[i] + 0.125*desirability - 0.125*decay
			self.activation_levels[i] = activation_level #between 0 and 1
			print emotion, self.activation_levels[i]
			if activation_level > activated_value:
				activate_emotion = emotion
				activated_value = activation_level
			
			self.file_writer.writerow(["difference", emotion, str(difference) + "\n"])
			self.file_writer.writerow(["elicitor level", emotion, str(self.elicitor_levels[i]) + "\n"])
			self.file_writer.writerow(["decay level ", emotion, str(decay) + "\n"])
			self.file_writer.writerow(["activation level ", emotion, str(activation_level) + "\n"])
			
			i += 1
		
		if activate_emotion is not None:
			print 'activate emotion ' + activate_emotion + ' activated emotion ' + activated_emotion
			self.mem().raiseEvent("Ginger/ActivatedEmotion", activate_emotion)
			return activate_emotion
		else:
			self.mem().raiseEvent("Ginger/ActivatedEmotion", activated_emotion)
			return activated_emotion
	
	def set_led(self, emotion):
		if emotion == "angry": #red
			color = "red"
		elif emotion == "sad": #gray
			color = 0x00b2b2b2
		elif emotion == "excited": #orange
			color = 0x00ff8d00
		elif emotion == "happy": #yellow/orange
			color = 0x00ffb400
		elif emotion == "calm": #blue
			color = "blue"
		
		self.file_writer.writerow(["color ", str(color) + "\n"])
		print 'color' + str(color)
		self.leds().fadeRGB("AllLeds", color, 0.1)
	
	def set_speech_style(self, emotion): #dependent on content
		if emotion == "angry": 
			#style = "\\style=neutral\\"
			style = "neutral"
		elif emotion == "sad": 
			#style = "\\style=neutral\\"
			style = "neutral"
		elif emotion == "excited":
			#style = "\\style=joyful\\"
			style = "joyful"
		elif emotion == "happy": 
			#style = "\\style=neutral\\"
			style = "neutral"
		elif emotion == "calm": 
			#style = "\\style=neutral\\"
			style = "neutral"
			
		#self.mem().insertData("Ginger/speechStyle", style)
		#self.mem().raiseEvent("Ginger/speechStyle", style)
		#self.ALDialog().setConcept("style","enu", style)
		self.file_writer.writerow(["style ", style + "\n"])
		print 'style' + style
		self.mem().insertData("Ginger/style", style)
		
		# if style == 2:
			# self.mem().insertData("Ginger/style") == 2
		# else: 
			# self.mem().insertData("Ginger/style") == 1
		
	def set_speech_rate(self, emotion):
		if emotion == "angry": 
			rate = 100
		elif emotion == "sad": 
			rate = 85
		elif emotion == "excited":
			rate = 105
		elif emotion == "happy": 
			rate = 100
		elif emotion == "calm": 
			rate = 95
		
		self.file_writer.writerow(["rate ", str(rate) + "\n"])
		print 'rate' + str(rate)
		self.tts().setParameter("speed", rate)
		
	def set_voice_pitch(self, emotion):
		if emotion == "angry": 
			#pitch = ["vct=110"]
			pitch = 110
		elif emotion == "sad": 
			#pitch = ["\\" + "vct=90" "\\"]
			pitch = 90
		elif emotion == "excited":
			#pitch = ["\\" + "vct=120" "\\"]
			pitch = 120
		elif emotion == "happy": 
			#pitch = ["\\" + "vct=110" "\\"]
			pitch = 110
		elif emotion == "calm": 
			#pitch = ["\\" + "vct=100" "\\"]
			pitch = 100
		
		self.file_writer.writerow(["pitch ", str(pitch) + "\n"])
		print 'pitch' + str(pitch)
		
		#self.mem().insertData("Ginger/voicePitch", pitch)
		#self.mem().raiseEvent("Ginger/voicePitch", pitch)
		#self.ALDialog().setConcept("pitch","enu", pitch)
		self.mem().insertData("Ginger/pitch", pitch)
	
	def set_speech_volume(self, emotion): #dependent on extraversion DONE
		if emotion == "angry": 
			volume = self.default_volume * 1.1
		elif emotion == "sad": 
			volume = self.default_volume * 0.9
		elif emotion == "excited":
			volume = self.default_volume * 1.2
		elif emotion == "happy": 
			volume = self.default_volume * 1.1
		elif emotion == "calm": 
			volume = self.default_volume
		
		volume = volume*(0.8+0.4*self.extraversion) #influencing volume with 0.8-1.2 with extraversion value 0-1
		#volume = ["\\vol=" + str(volume) + "\\"]
		#self.mem().insertData("Ginger/speechVolume", volume)
		#self.mem().raiseEvent("Ginger/speechVolume", volume)
		self.file_writer.writerow(["volume ", str(volume) + "\n"])
		print 'volume' + str(volume)
		#self.ALDialog().setConcept("volume","enu", volume)
		#self.mem().insertData("Ginger/volume", volume)
		
	def set_gesture_size(self, emotion): #dependent on extraversion DONE
		if emotion == "angry": 
			size = 1.0
		elif emotion == "sad": 
			size = 0.6
		elif emotion == "excited":
			size = 1.0
		elif emotion == "happy": 
			size = 0.9
		elif emotion == "calm": 
			size = 0.75
		
		size = (size+self.extraversion)/2
		self.file_writer.writerow(["gesture size ", str(size) + "\n"])
		print 'gesture size' + str(size)
		names = "LArm"
		stiffnessLists = size
		timeLists = 1.0
		self.ms().stiffnessInterpolation(names, stiffnessLists, timeLists)
		names = "RArm"
		stiffnessLists = size
		timeLists = 1.0	
		self.ms().stiffnessInterpolation(names, stiffnessLists, timeLists)
		
	def set_position(self, emotion):  #dependent on extraversion DONE
		names = "HeadPitch"
		useSensors = True
		current_angles = self.ms().getAngles(names, useSensors)
		
		chance = random.randint(0,2)
		
		if emotion == "sad" and (current_angles < 0): #if sad always look down
			set_angles = 0.3
		elif emotion == "excited" and (current_angles > 0): #if excited always look up
			set_angles = -0.3
		elif (current_angles < 0) and (self.extraversion < 0.5): #looking up and introvert, then chance 33% to look down
			if chance == 0:
				set_angles = 0.2
		elif (current_angles > 0) and (self.extraversion > 0.5): #looking down and extravert, then look up
			set_angles = -0.2
		else: set_angles = current_angles
		
		self.file_writer.writerow(["head angle ", str(set_angles) + "\n"])
		print 'head angle' + str(set_angles)
		self.ms().setAngles(names, set_angles, 0.2)
	
	def reset_emotion_values(self):
		emotion = self.emotion[0]
		i = self.emotions.index(emotion)
		self.decay_levels[i] = 0.0
				
	def on_user_values(self): #calculate activated emotion robot with user values
		print 'on user values'
		# if (self.face_arousal is not None) and (self.voice_arousal != 0):
			# user_valence = (self.face_valence+self.voice_valence)/2
			# user_arousal = (self.face_arousal+self.voice_arousal)/2
		# elif self.face_arousal is not None:
			# user_valence = self.face_valence
			# user_arousal = self.face_arousal
		# else:
			# user_valence = None
			# user_arousal = None
			
		if self.voice_arousal != 0:
			user_valence = (self.face_valence+self.voice_valence)/2
			user_arousal = (self.face_arousal+self.voice_arousal)/2
		else:
			user_valence = self.face_valence
			user_arousal = self.face_arousal
		
		self.file_writer.writerow(["user emotion values: ", user_valence, user_arousal + "\n"])
		
		valence = self.calculate_valence_robot(user_valence)
		arousal = self.calculate_arousal_robot(user_arousal)
		
		self.file_writer.writerow(["robot emotion values: ", valence, arousal + "\n"])
		sentence = "Valence: " + str(valence) + " Arousal: " + str(arousal)
		#self.mem().raiseEvent("Ginger/ChatAnswer", sentence)
		
		activate_emotion = self.calculate_activate_emotion()
		if self.emotion[0] == activate_emotion:
			self.emotion[1] += 1
		else: 
			self.reset_emotion_values()
			self.emotion[0] = activate_emotion
			self.emotion[1] = 1
		
		self.file_writer.writerow(["activated emotion", activate_emotion + "\n"])
		sentence = "My emotion is: " + activate_emotion
		#self.mem().raiseEvent("Ginger/ChatAnswer", sentence)
		self.on_activated_emotion(activate_emotion)
		#self.mem().raiseEvent("Ginger/ActivatedEmotion", self.emotion[0])
	
	def on_activated_emotion(self, emotion): #raise events to express emotion
		#set decay value emotion
		i = self.emotions.index(emotion)
		if self.decay_levels[i] == 0.0:
			self.decay_levels[i] = 0.25
		else:
			self.decay_levels[i] *= 1.5 #decay increases exponentially with 50%
		if self.decay_levels[i] > 1.0:
			self.decay_levels[i] = 1.0
		
		#express emotion		
		self.set_led(emotion)
		self.set_speech_style(emotion)
		self.set_speech_rate(emotion)
		self.set_voice_pitch(emotion)
		self.set_speech_volume(emotion)
		self.set_gesture_size(emotion)
		#self.set_position(emotion)
		
		self.face_valence = 0.0
		self.face_arousal = 0.0
		self.voice_valence = 0.0
		self.voice_arousal = 0.0
		self.occurrence = 0.0
		
	def on_face_emotion(self, emotion):
		if emotion is not None:
			if emotion == "sadness":
				self.face_valence = -0.5
				self.face_arousal = -0.5
			elif emotion == "happiness":
				self.face_valence = 0.75
				self.face_arousal = 0.25
			elif emotion == "contempt": #TO BE DEFINED
				self.face_valence = -0.25
				self.face_arousal = -0.5
			elif emotion == "disgust": #TO BE DEFINED
				self.face_valence = -0.5
				self.face_arousal = -0.25
			elif emotion == "anger":
				self.face_valence = -0.5
				self.face_arousal = 0.5
			elif emotion == "surprise":
				self.face_valence = 0.25
				self.face_arousal = 0.75
			elif emotion == "fear": #TO BE DEFINED
				self.face_valence = -1.0
				self.face_arousal = 0.0
			else: #emotion == "neutral"
				self.face_valence = 0.0
				self.face_arousal = 0.0
		else: 
			self.face_valence = None
			self.face_arousal = None
		
		if self.face_valence is not None:
			sentence = "face Valence: " + str(self.face_valence) + " face Arousal: " + str(self.face_arousal)
			self.file_writer.writerow(["recognized face emotion: ", emotion, str(self.face_valence), str(self.face_arousal) + "\n"])
		else: sentence = 'no face recognized'
		#self.mem().raiseEvent("Ginger/ChatAnswer", sentence)
		
	def on_occurrence(self, occurrence):
		#self.mem().raiseEvent("Ginger/GetExpression", 1)
		print 'on occurrence', occurrence
		if occurrence == "positive":
			self.occurrence = 1
		elif occurrence == "negative":
			self.occurrence = -1
		else:
			self.occurrence = 0
		
		self.file_writer.writerow(["recognized occurrence: ", occurrence, str(self.occurrence) + "\n"])
			
		self.on_user_values()
		
	def on_voice_emotion(self, eventEmo):
		print eventEmo
		matched_emotion_index = eventEmo[0][0]
		matched_emotion_level = eventEmo[0][1]
		exitement_level = eventEmo[2]
		
		if matched_emotion_index == 1: #calm
			self.voice_valence = 0.25
			self.voice_arousal =  -0.25
		elif matched_emotion_index == 2: #anger
			self.voice_valence = -0.5
			self.voice_arousal = 0.5
		elif matched_emotion_index == 3: #joy
			self.voice_valence = 0.75
			self.voice_arousal = 0.25
		elif matched_emotion_index == 4: #sorrow
			self.voice_valence = -0.5
			self.voice_arousal = -0.5
		else: #unknown
			self.voice_valence = 0.0
			self.voice_arousal = 0.0
		
		self.file_writer.writerow(["recognized voice emotion: ", str(self.voice_valence), str(self.voice_arousal) + "\n"])
		
		#sentence = "Voice Valence: " + str(self.voice_valence) + " Voice Arousal: " + str(self.voice_arousal)
		#self.mem().raiseEvent("Ginger/ChatAnswer", sentence)
		
	def setALMemorySubscription(self, subscribe):
		self.subscribingLock.acquire()
		if subscribe:
			self.voice_emotion = self.mem().subscriber("ALVoiceEmotionAnalysis/EmotionRecognized")
			self.voice_emotion.signal.connect(self.on_voice_emotion)
			self.dialog_occurrence = self.mem().subscriber("Ginger/occurrence")
			self.dialog_occurrence.signal.connect(self.on_occurrence)
			self.face_emotion = self.mem().subscriber("Ginger/faceEmotion")
			self.face_emotion.signal.connect(self.on_face_emotion)
			self.user_values = self.mem().subscriber("Ginger/ValuesUser")
			self.user_values.signal.connect(self.on_user_values)
			#self.activated_emotion = self.mem().subscriber("Ginger/ActivatedEmotion")
			#self.activated_emotion.signal.connect(self.on_activated_emotion)
		else:
			self.voice_emotion.signal.disconnect("ALVoiceEmotionAnalysis/EmotionRecognized")
			self.dialog_occurrence.signal.disconnect("Ginger/occurrence")
			self.face_emotion.signal.disconnect("Ginger/faceEmotion")
			self.user_values.signal.disconnect("Ginger/ValuesUser")
			#self.activated_emotion.signal.disconnect("Ginger/ActivatedEmotion")
	
		self.subscribingLock.release()
	
def main():
	import sys
	app = qi.Application(sys.argv)
	app.start()

	emotion_robot = EmotionRobot(app.session)
	id = app.session.registerService(emotion_robot.module_name, emotion_robot)
	emotion_robot.start()

	app.run()
	sys.exit()

if __name__ == '__main__':
	main()