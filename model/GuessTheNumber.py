import time

import random

from core.base.SuperManager import SuperManager
from core.base.model.Intent import Intent
from core.dialog.model.DialogSession import DialogSession
from .MiniGame import MiniGame


class GuessTheNumber(MiniGame):

	_INTENT_PLAY_GAME = Intent('PlayGame')
	_INTENT_ANSWER_YES_OR_NO = Intent('AnswerYesOrNo')
	_INTENT_ANSWER_NUMBER = Intent('AnswerNumber')

	def __init__(self):
		super().__init__()
		self._number = 0
		self._start: float = 0


	@property
	def intents(self) -> list:
		return [
			self._INTENT_ANSWER_NUMBER
		]


	def start(self, session: DialogSession):
		super().start(session)

		redQueen = SuperManager.getInstance().SkillManager.getSkillInstance('RedQueen')
		redQueen.changeRedQueenStat('happiness', 10)

		self._number = random.randint(1, 10000)

		self._start = time.time() - 4

		SuperManager.getInstance().MqttManager.continueDialog(
			sessionId=session.sessionId,
			text=SuperManager.getInstance().TalkManager.randomTalk(talk='guessTheNumberStart', skill='Minigames'),
			intentFilter=[self._INTENT_ANSWER_NUMBER]
		)


	def onMessage(self, session: DialogSession):
		if session.intentName == self._INTENT_ANSWER_NUMBER:
			self.numberIntent(session)


	def numberIntent(self, session: DialogSession):
		number = int(session.slotValue('Number'))
		if number == self._number:

			score = round(time.time() - self._start)
			minutes, seconds = divmod(score, 60)
			scoreFormatted = SuperManager.getInstance().LanguageManager.getTranslations(skill='Minigames', key='minutesAndSeconds')[0].format(round(minutes), round(seconds))

			self.sound('applause', session.deviceUid)

			SuperManager.getInstance().mqttManager.endDialog(
				sessionId=session.sessionId,
				text=SuperManager.getInstance().TalkManager.randomTalk('guessTheNumberCorrect', 'Minigames').format(self._number, self._number)
			)

			textType = 'guessTheNumberScore'
			if session.user != 'unknown' and SuperManager.getInstance().SkillManager.getSkillInstance('Minigames').checkAndStoreScore(user=session.user, score=score, biggerIsBetter=False):
				textType = 'guessTheNumberNewHighscore'

			SuperManager.getInstance().mqttManager.say(
				deviceUid=session.deviceUid,
				text=SuperManager.getInstance().TalkManager.randomTalk(textType, 'Minigames').format(scoreFormatted),
				canBeEnqueued=True
			)

			SuperManager.getInstance().mqttManager.ask(
				text=SuperManager.getInstance().TalkManager.randomTalk('playAgain', 'Minigames'),
				intentFilter=[self._INTENT_ANSWER_YES_OR_NO],
				customData={
					'speaker': session.user,
					'askRetry': True
				}
			)
			return

		textType = 'guessTheNumberLess'
		if number < self._number:
			textType = 'guessTheNumberMore'

		SuperManager.getInstance().MqttManager.continueDialog(
			sessionId=session.sessionId,
			text=SuperManager.getInstance().TalkManager.randomTalk(textType, 'Minigames'),
			intentFilter=[self._INTENT_ANSWER_NUMBER]
		)
