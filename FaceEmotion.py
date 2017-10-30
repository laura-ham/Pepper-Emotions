########### Python 2.7 #############
import httplib, urllib, base64, json
import os, sys, time, qi, threading
from naoqi import ALProxy

class FaceEmotion(object):
	def __init__(self, session):
		self.PACKAGE_UUID = "EmotionProject" #Package ID of the Choregraph project
		self.session = session
		self.module_name = "FaceEmotion"
		self.headers = {
		# Request headers. Replace the placeholder key below with your subscription key.
		'Content-Type': 'application/octet-stream',
		'Ocp-Apim-Subscription-Key': 'YOUR KEY'',
		}

		self.params = urllib.urlencode({
		})
		
	def start(self):
		self.subscribingLock = threading.Lock()
		self.setALMemorySubscription(True)
		print self.module_name, "service started..."
		
		self.photoCapture().setResolution(3)
		self.photoCapture().setPictureFormat("jpg")
		
	def stop(self):
		self.stop_resetchat()
		self.setALMemorySubscription(False)
	
	def on_get_emotion(self, message):
		#val = self.mem().getData("FaceDetected", 0)
		#if(val and isinstance(val, list) and len(val) == 2):
		self.take_picture()
		#self.mem().raiseEvent("Ginger/ChatAnswer", "picture taken")
		body = self.get_picture()
		#self.mem().raiseEvent("Ginger/ChatAnswer", "get picture")
		data = self.get_data(self.params, body, self.headers)
		#self.mem().raiseEvent("Ginger/ChatAnswer", data)
		if data == False:
			self.on_face_emotion(None)
		else:
			emotion = self.get_emotion(data)
			#self.mem().raiseEvent("Ginger/ChatAnswer", emotion)
			#user_values = self.get_user_values(emotion)
			#self.mem().raiseEvent("Ginger/ChatAnswer", user_values)
			#self.on_user_values(user_values)
			self.on_face_emotion(emotion)
			sentence = "face emotion = " + emotion
			#self.mem().raiseEvent("Ginger/ChatAnswer", sentence)
		#else: self.on_face_emotion(None)
			
	def on_face_emotion(self, emotion):
		self.mem().raiseEvent("Ginger/faceEmotion", emotion)
	
	def get_emotion(self, data):
		try:
			scores = data["scores"]
			emotion_score = 0
			highest_emotion = None
			for emotion in scores:
				score = scores[str(emotion)]
				if score > emotion_score:
					highest_emotion = emotion
					emotion_score = score
			return highest_emotion
		except: self.mem().raiseEvent("Ginger/faceEmotion", "neutral")

	def get_data(self, params, body, headers):
		try:
			conn = httplib.HTTPSConnection('westus.api.cognitive.microsoft.com')
			conn.request("POST", "/emotion/v1.0/recognize?%s" % params, body, headers)
			response = conn.getresponse()
			data = response.read()
			data = json.loads(data)[0]
			conn.close()
			#self.mem().raiseEvent("Ginger/ChatAnswer", data)
			if len(data) < 2:
				return False
			return data
		except Exception as e:
			print("[Errno {0}] {1}".format(e.errno, e.strerror))
		
	def get_picture(self):
		path = "/home/nao/recordings/cameras/image.jpg" 
		with open( path, 'rb' ) as f:
			body = f.read()
		return body
	
	def take_picture(self):
		self.photoCapture().takePicture("/home/nao/recordings/cameras/", "image")
		return
		
	def mem(self):
		return self.session.service("ALMemory")
	
	def photoCapture(self):
		return self.session.service("ALPhotoCapture")
	
	def ALDialog(self):
		return self.session.service("ALDialog")
		
	def FaceDetection(self):
		return self.session.service("ALFaceDetection")
	
	def setALMemorySubscription(self, subscribe):
		self.subscribingLock.acquire()
		if subscribe:
			self.face_emo = self.mem().subscriber("Ginger/GetExpression")
			self.face_emo.signal.connect(self.on_get_emotion)
		else:
			self.face_emo.signal.disconnect("Ginger/GetExpression")
			
		self.subscribingLock.release()
		
def main():
	import sys
	app = qi.Application(sys.argv)
	app.start()

	face_emotion = FaceEmotion(app.session)
	id = app.session.registerService(face_emotion.module_name, face_emotion)
	face_emotion.start()

	app.run()
	sys.exit()

if __name__ == '__main__':
	main()
