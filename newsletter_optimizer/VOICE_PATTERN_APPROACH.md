# Voice Pattern Approach (Not Raw Text Copying)

## The Right Way to Transfer Voice

### ❌ WRONG: Show Full Past Newsletter Text
```
# EXAMPLES FROM YOUR PAST NEWSLETTERS
"""
[800 characters of actual past newsletter text]
"""
```

**Problems**:
- Model will **copy-paste** phrases instead of generating fresh content
- **Stale examples** get reused verbatim
- Leads to **repetitive** newsletters
- Model learns CONTENT, not STYLE

### ✅ RIGHT: Extract and Show Voice PATTERNS
```
## YOUR VOICE AND STYLE
Tone: Critical, direct, journalistic - no smoothing over
Energy: Sharp observations, punchy delivery
Sentence rhythm: Short impactful sentences mixed with longer analytical ones
Paragraphs: 2-4 sentences max, frequent breaks for readability
How you open: Direct statement of what happened, then why it matters
How you argue: Evidence first, then interpretation, end with implications
Transitions: Minimal - jump to next point, trust reader to follow

# VOICE PATTERNS (rhetorical moves)
- Critical Observation: Pattern for calling out hypocrisy or contradiction | use_as: main argument
- Context Drop: Brief background to ground unfamiliar readers | use_as: setup
- Implication Punch: "And that means..." ending that lands the point | use_as: conclusion
```

**Advantages**:
- Model learns **HOW you write**, not WHAT you wrote
- Generates **fresh content** in your style
- **Adaptable** to any topic
- Transfers **voice/attitude**, not words

## What We Actually Use

### From Newsletter Bible (Extracted Patterns):

1. **`writing_voice`**: 
   - Tone, energy, rhythm, paragraph style
   - How you open, argue, transition
   - **NOT** full sentences

2. **`structure_patterns`**:
   - Typical sections
   - Opening style (HOW, not exact text)
   - Closing style

3. **`headline_formulas`**:
   - Pattern: "X is Y and Z is loving it"
   - Pattern: "Why X matters for Y"
   - **NOT** copying old headlines

4. **`rules_for_success`**:
   - "Keep intro under 3 sentences"
   - "Always connect to reader's work"
   - Extracted learnings, not examples

5. **`cliches_to_avoid`** (59 total):
   - "Let's dive into"
   - "silver lining"
   - "gripping scenario"
   - Explicit ban list

6. **`signature_words`**:
   - Words you use frequently (15 shown)
   - Vocabulary fingerprint

### From RelevanceBrief (Rhetorical Moves):

```
# VOICE PATTERNS (rhetorical moves)
- Opening Hook Pattern: How you typically grab attention | use_as: intro
- Sarcastic Contrast: When X does Y despite claiming Z | use_as: critique
- Reader Reality Check: What this means for your newsroom | use_as: practical
```

These are **EXTRACTED patterns**, not copied sentences.

### Opening Style Snippets (100 chars):

```
# YOUR OPENING STYLE (patterns to match, not text to copy)
- Opening pattern: "X happened this week. Here's why it matters..."
- Opening pattern: "We need to talk about X. Not because..."
```

**Why 100 chars?**
- Enough to see the **PATTERN** (direct statement → why it matters)
- Too short to **copy verbatim**
- Shows **HOW** you open, not a template to fill in

## How This Prevents the 3 Problems

### Problem 1: Wrong Attribution (Wired → NYT)
**Solution**: Source attribution warning + publication names extracted from URLs
```
## ⚠️ ATTRIBUTION WARNING: Cite these sources ACCURATELY!
- **Wired**: [article title]
- **Wired**: [another article]
```

### Problem 2: Full of Clichés
**Solution**: Explicit ban list (59 clichés) + anti-ChatGPT rules
```
## CRITICAL RULES
2. DO NOT use generic AI writing patterns like "Let's dive into", "gripping scenario", "silver lining"
3. DO NOT write like ChatGPT - avoid formulaic transitions, corporate jargon
```

### Problem 3: Not Your Voice
**Solution**: Show PATTERNS of how you write, not what you wrote
```
How you argue: Evidence first, then interpretation, end with implications
Sentence rhythm: Short impactful sentences mixed with longer analytical ones
```

## System Prompt Structure (What Model Sees)

```
You are Paul McNally, writing your "Develop AI" newsletter...

## YOUR VOICE AND STYLE
Tone: Critical, direct, journalistic - no smoothing over
Energy: Sharp observations, punchy delivery
Sentence rhythm: Short impactful mixed with longer analytical
Paragraphs: 2-4 sentences max
How you open: Direct statement → why it matters
How you argue: Evidence → interpretation → implications
Transitions: Minimal, trust reader to follow

## HOW YOU STRUCTURE A NEWSLETTER
- Typical sections: Hook, Main Story, Implications, Call-to-Action
- Openings: Direct news statement, not scene-setting
- Closings: Practical takeaway for newsrooms

Headline patterns that work for you:
- [Pattern]: "X is Y and Z is loving it"
- [Pattern]: "Why X matters for Y"

Rules that drive performance:
- Keep intro under 3 sentences
- Always connect to reader's work
- Use concrete examples, not abstractions
- End sections with "so what?" answer

Cliches and weak phrases to avoid:
Let's dive into, silver lining, gripping scenario, unpack, [56 more...]

## CRITICAL RULES
1. Write EXACTLY like Paul McNally - match his voice, cadence, sentence structure
2. DO NOT use generic AI patterns
3. DO NOT write like ChatGPT
4. Use Paul's direct, critical, journalistic style - sharp observations, not smoothed over
5. Reference sources ACCURATELY - check publication names
6. Keep energy authentic - critical when needed, not artificially balanced
7. Use short paragraphs, varied sentence length, conversational rhythm
```

## User Prompt Structure (What Model Generates From)

```
# YOUR OPENING STYLE (patterns to match, not text to copy)
- Opening pattern: "X happened. Here's why it matters..."
- Opening pattern: "We need to talk about X. Not because..."

# VOICE PATTERNS (rhetorical moves)
- Critical Observation: Pattern for calling out hypocrisy | use_as: main argument
- Context Drop: Brief background to ground readers | use_as: setup
- Implication Punch: "And that means..." ending | use_as: conclusion

# PROVIDED SOURCES
## ⚠️ ATTRIBUTION WARNING: Cite these sources ACCURATELY!
- **Wired**: Grok Is Being Used to Mock and Strip Women...
- **Wired**: X Didn't Fix Grok's 'Undressing' Problem...

# ANCHORED OUTLINE
[Bullets with anchor IDs, not full text]

# INSTRUCTIONS
3. CRITICAL: Write in Paul McNally's voice - study the patterns above and match:
   - His sentence rhythm and paragraph length
   - His critical, journalistic tone (not smoothed over)
   - His direct observations and sharp takes
   - NO ChatGPT phrases: no 'dive into', 'silver lining', 'unpack'
4. ATTRIBUTION: Double-check source publications - cite Wired as Wired, NYT as NYT
```

## What You'll See in Regenerated Prompt

✅ **No full past newsletter text**
✅ **Voice patterns** (tone, rhythm, how you argue)
✅ **Opening style snippets** (100 chars showing PATTERN)
✅ **Rhetorical moves** (title + summary + use_as)
✅ **Explicit anti-ChatGPT rules**
✅ **Source attribution warnings**

## How to Verify

After regenerating the prompt:

1. Search for: `# EXAMPLES FROM YOUR PAST NEWSLETTERS`
   - ❌ Should NOT exist
   
2. Search for: `# YOUR OPENING STYLE`
   - ✅ Should exist with SHORT snippets (100 chars)
   
3. Search for: `# VOICE PATTERNS`
   - ✅ Should exist with rhetorical move patterns
   
4. Search for: `⚠️ ATTRIBUTION WARNING`
   - ✅ Should exist with **Wired**, **NYT**, etc. clearly labeled

5. Search for: `DO NOT use generic AI writing patterns`
   - ✅ Should exist in instructions

## Result: Fresh Content in Your Voice

**Before** (copying past text):
> "In 2020 I wrote about DeepNude. Four years later, we're seeing the same patterns emerge with Grok."
> *(Recycled observation from past newsletter)*

**After** (using voice patterns):
> "Grok started as a vanity project. Now it's creating deepfakes of women in hijabs, and Musk's treating the controversy as free advertising."
> *(Fresh observation in your critical, direct style)*

Same **voice/attitude**, different **content**.

---

**Status**: ✅ Pattern-based voice transfer (not raw text copying)  
**Approach**: Extract HOW you write, not WHAT you wrote  
**Result**: Fresh content that sounds like you, not recycled phrases
