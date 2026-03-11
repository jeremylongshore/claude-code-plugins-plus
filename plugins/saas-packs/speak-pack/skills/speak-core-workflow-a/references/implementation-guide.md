# Speak Core Workflow A - Implementation Guide

Detailed implementation reference for the speak-core-workflow-a skill.

## Instructions

### Step 1: Initialize Conversation Session
```typescript
// src/workflows/conversation-practice.ts
import {
  SpeakClient,
  AITutor,
  ConversationSession,
  ConversationConfig,
} from '@speak/language-sdk';

interface ConversationPracticeConfig {
  targetLanguage: string;
  nativeLanguage: string;
  topic: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: number; // minutes
  focusAreas?: ('pronunciation' | 'grammar' | 'vocabulary' | 'fluency')[];
}

async function initializeConversation(
  client: SpeakClient,
  config: ConversationPracticeConfig
): Promise<ConversationSession> {
  const tutor = new AITutor(client, {
    targetLanguage: config.targetLanguage,
    nativeLanguage: config.nativeLanguage,
    proficiencyLevel: config.difficulty,
    personality: 'encouraging', // or 'strict', 'casual'
  });

  const session = await tutor.startConversation({
    topic: config.topic,
    maxDuration: config.duration * 60 * 1000, // Convert to ms
    focusAreas: config.focusAreas || ['pronunciation', 'grammar'],
    adaptiveDifficulty: true,
  });

  return session;
}
```

### Step 2: Implement Conversation Loop
```typescript
interface ConversationExchange {
  tutorPrompt: {
    text: string;
    audioUrl: string;
    translation?: string;
  };
  userResponse: {
    text: string;
    audioData?: ArrayBuffer;
  };
  feedback: {
    pronunciationScore: number;
    grammarCorrections: GrammarCorrection[];
    suggestions: string[];
    encouragement: string;
  };
}

async function runConversationLoop(
  session: ConversationSession,
  onExchange: (exchange: ConversationExchange) => void
): Promise<ConversationSummary> {
  const exchanges: ConversationExchange[] = [];

  while (!session.isComplete) {
    // Get AI tutor's prompt
    const tutorPrompt = await session.getNextPrompt();

    // Display prompt to user (with audio playback)
    console.log(`\nTutor: ${tutorPrompt.text}`);
    if (tutorPrompt.translation) {
      console.log(`(${tutorPrompt.translation})`);
    }

    // Get user's response (from speech recognition or text input)
    const userResponse = await getUserResponse();

    // Submit response and get feedback
    const feedback = await session.submitResponse({
      text: userResponse.text,
      audioData: userResponse.audioData,
    });

    const exchange: ConversationExchange = {
      tutorPrompt,
      userResponse,
      feedback,
    };

    exchanges.push(exchange);
    onExchange(exchange);

    // Display feedback
    displayFeedback(feedback);

    // Check if session should continue
    if (feedback.shouldEndSession) {
      break;
    }
  }

  return session.getSummary();
}
```

### Step 3: Handle Real-time Pronunciation Feedback
```typescript
interface PronunciationFeedback {
  overall: number;
  words: WordScore[];
  phonemes?: PhonemeScore[];
  suggestions: string[];
}

interface WordScore {
  word: string;
  score: number;
  issue?: 'stress' | 'tone' | 'length' | 'pronunciation';
  suggestion?: string;
}

function displayFeedback(feedback: ConversationExchange['feedback']) {
  console.log(`\n--- Feedback ---`);
  console.log(`Pronunciation: ${feedback.pronunciationScore}/100`);

  if (feedback.grammarCorrections.length > 0) {
    console.log('\nGrammar corrections:');
    for (const correction of feedback.grammarCorrections) {
      console.log(`  "${correction.original}" → "${correction.corrected}"`);
      console.log(`  Explanation: ${correction.explanation}`);
    }
  }

  if (feedback.suggestions.length > 0) {
    console.log('\nSuggestions:');
    feedback.suggestions.forEach(s => console.log(`  • ${s}`));
  }

  console.log(`\n${feedback.encouragement}`);
}
```

### Step 4: Generate Session Summary
```typescript
interface ConversationSummary {
  sessionId: string;
  duration: number;
  topic: string;
  totalExchanges: number;
  averagePronunciationScore: number;
  vocabularyUsed: VocabularyItem[];
  grammarPatternsPracticed: string[];
  areasForImprovement: string[];
  achievements: Achievement[];
  nextLessonSuggestion: string;
}

async function generateSessionSummary(
  session: ConversationSession
): Promise<ConversationSummary> {
  const summary = await session.getSummary();

  return {
    ...summary,
    // Calculate metrics
    averagePronunciationScore: calculateAveragePronunciation(summary.exchanges),
    vocabularyUsed: extractVocabulary(summary.exchanges),
    grammarPatternsPracticed: extractGrammarPatterns(summary.exchanges),
    areasForImprovement: analyzeWeakAreas(summary.exchanges),
    achievements: checkAchievements(summary),
    nextLessonSuggestion: suggestNextLesson(summary),
  };
}
```


## Complete Workflow Example

```typescript
// Full conversation practice workflow
async function conversationPracticeWorkflow() {
  const client = getSpeakClient();

  // Configure session
  const config: ConversationPracticeConfig = {
    targetLanguage: 'es',
    nativeLanguage: 'en',
    topic: 'ordering_food_restaurant',
    difficulty: 'intermediate',
    duration: 10, // 10 minutes
    focusAreas: ['pronunciation', 'vocabulary'],
  };

  console.log('Starting conversation practice...');
  console.log(`Topic: ${config.topic}`);
  console.log(`Language: ${config.targetLanguage}`);

  // Initialize session
  const session = await initializeConversation(client, config);

  // Run conversation loop
  const summary = await runConversationLoop(session, (exchange) => {
    // Real-time callback for each exchange
    trackProgress(exchange);
  });

  // Display summary
  console.log('\n========== Session Complete ==========');
  console.log(`Duration: ${Math.round(summary.duration / 60000)} minutes`);
  console.log(`Exchanges: ${summary.totalExchanges}`);
  console.log(`Average Pronunciation: ${summary.averagePronunciationScore}/100`);

  if (summary.achievements.length > 0) {
    console.log('\nAchievements earned:');
    summary.achievements.forEach(a => console.log(`  🏆 ${a.name}`));
  }

  console.log(`\nSuggested next lesson: ${summary.nextLessonSuggestion}`);

  return summary;
}
```


## Topic Categories
| Category | Example Topics |
|----------|----------------|
| Daily Life | greetings, shopping, directions |
| Travel | hotel_booking, restaurant, transportation |
| Work | meetings, presentations, negotiations |
| Social | making_friends, parties, small_talk |
| Culture | holidays, traditions, food |

