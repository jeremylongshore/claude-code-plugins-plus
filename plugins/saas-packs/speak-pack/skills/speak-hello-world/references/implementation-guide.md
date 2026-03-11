# Speak Hello World - Implementation Guide

Detailed implementation reference for the speak-hello-world skill.

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world lesson.

### Step 2: Import and Initialize Client
```typescript
// src/speak-hello-world.ts
import { SpeakClient, LessonSession, AITutor } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'es', // Learning Spanish
});
```

### Step 3: Create Your First Lesson Session
```typescript
async function startFirstLesson() {
  // Initialize AI tutor
  const tutor = new AITutor(client, {
    targetLanguage: 'es',
    nativeLanguage: 'en',
    proficiencyLevel: 'beginner',
  });

  // Start a conversation practice session
  const session = await tutor.startSession({
    topic: 'greetings',
    duration: 5, // 5 minutes
  });

  // Get AI tutor's opening prompt
  const opening = await session.getPrompt();
  console.log('AI Tutor says:', opening.text);
  console.log('Audio URL:', opening.audioUrl);

  // Simulate user response (in production, use speech recognition)
  const feedback = await session.submitResponse({
    text: 'Hola, me llamo Juan',
    audioData: null, // Optional: audio buffer for pronunciation scoring
  });

  console.log('Feedback:', feedback.message);
  console.log('Pronunciation:', feedback.pronunciationScore);
  console.log('Grammar:', feedback.grammarCorrections);

  return session;
}

startFirstLesson().catch(console.error);
```

### Step 4: Run Your First Lesson
```bash
npx tsx src/speak-hello-world.ts
```


## Detailed Examples

### TypeScript: Pronunciation Practice
```typescript
import { SpeakClient, PronunciationPractice } from '@speak/language-sdk';

const client = new SpeakClient({
  apiKey: process.env.SPEAK_API_KEY!,
  appId: process.env.SPEAK_APP_ID!,
  language: 'ko',
});

async function practicePronunciation() {
  const practice = new PronunciationPractice(client);

  // Get a phrase to practice
  const phrase = await practice.getPhrase({
    difficulty: 'easy',
    category: 'daily_conversation',
  });

  console.log('Practice this phrase:');
  console.log('Korean:', phrase.text);
  console.log('Romanization:', phrase.romanization);
  console.log('English:', phrase.translation);
  console.log('Listen:', phrase.audioUrl);
}

practicePronunciation();
```

### Python: Basic Lesson
```python
from speak_sdk import SpeakClient, AITutor

client = SpeakClient(
    api_key=os.environ.get('SPEAK_API_KEY'),
    app_id=os.environ.get('SPEAK_APP_ID'),
    language='ja'
)

async def first_lesson():
    tutor = AITutor(client, target_language='ja', native_language='en')
    session = await tutor.start_session(topic='self_introduction')

    prompt = await session.get_prompt()
    print(f"Tutor: {prompt.text}")

    # Submit response
    feedback = await session.submit_response(text="Hajimemashite, watashi wa John desu")
    print(f"Feedback: {feedback.message}")

asyncio.run(first_lesson())
```

### Vocabulary Quiz Example
```typescript
async function vocabularyQuiz() {
  const quiz = await client.vocabulary.createQuiz({
    language: 'es',
    topic: 'food',
    questionCount: 5,
    type: 'multiple_choice',
  });

  for (const question of quiz.questions) {
    console.log(`Q: ${question.prompt}`);
    console.log(`Options: ${question.options.join(', ')}`);

    // In production, get user input
    const answer = await quiz.submitAnswer(question.id, 'answer_a');
    console.log(`Correct: ${answer.correct}`);
  }

  console.log(`Final Score: ${quiz.score}/${quiz.total}`);
}
```

