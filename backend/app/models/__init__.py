"""All SQLAlchemy models. Importing this package registers every table on Base.metadata."""
from app.models.user import User, UserPreferences
from app.models.language import Language
from app.models.vocabulary import (
    CollectionCard,
    VocabularyCard,
    VocabularyCollection,
    VocabularyExample,
    VocabularyGrammar,
)
from app.models.ingest import AudioRecording, ExtractionJob, SpeechTranscript, UploadedDocument
from app.models.learning import (
    DailyLearningGoal,
    LearningStatistic,
    PronunciationAttempt,
    ReviewHistory,
    ReviewSession,
    TutorConversation,
    TutorMessage,
    UserMistake,
)

__all__ = [
    "User", "UserPreferences", "Language", "VocabularyCard", "VocabularyExample", "VocabularyGrammar",
    "VocabularyCollection", "CollectionCard", "UploadedDocument", "ExtractionJob", "AudioRecording",
    "SpeechTranscript", "ReviewSession", "ReviewHistory", "LearningStatistic", "TutorConversation",
    "TutorMessage", "PronunciationAttempt", "DailyLearningGoal", "UserMistake",
]
