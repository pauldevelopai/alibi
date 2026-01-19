"""
Story Types - Categorization of main newsletter story types

Defines the broad thematic categories for newsletter main stories.
"""

# Main story types based on analysis of 44 Develop AI newsletters
STORY_TYPES = {
    'how_to_tutorial': {
        'name': 'How-To / Tutorial',
        'icon': '🛠️',
        'description': 'Practical guide showing readers how to do something with AI',
        'headline_patterns': [
            'How to [action] with AI',
            'A few clicks to build your own [thing]',
            'Building a [project] step by step',
            '[Number] tips for [goal]',
        ],
        'examples': [
            'How to build your own AI model and trap it in your house',
            'A few clicks to build your own AI chatbot',
            'How to plug WhatsApp directly into ChatGPT',
            'Use AI to Build a Complete Podcast Workflow',
        ],
        'tone': 'Practical, instructive, encouraging',
        'open_rate_impact': '+13% (best performer)',
    },
    
    'news_analysis': {
        'name': 'News Analysis',
        'icon': '📰',
        'description': 'Breaking down recent AI news and what it means',
        'headline_patterns': [
            '[Company/Entity] has [done something]',
            '[Event] just happened - here\'s what it means',
            'The latest on [topic]',
            '[Topic] update: what you need to know',
        ],
        'examples': [
            'Zimbabwe has built an AI newsreader, but she isn\'t coming for your job',
            'The AI Wars Have Begun: Apple vs the BBC',
            'AI strategies for newsrooms... and the content apocalypse',
        ],
        'tone': 'Informative, analytical, timely',
        'open_rate_impact': 'Average',
    },
    
    'opinion_take': {
        'name': 'Opinion / Hot Take',
        'icon': '💭',
        'description': 'Strong personal perspective on an AI topic',
        'headline_patterns': [
            'Why [controversial statement]',
            '[Topic] is [strong opinion]',
            'We need to talk about [issue]',
            'The truth about [topic]',
        ],
        'examples': [
            'AI So White... and why the AI "white racism" at Google was overblown',
            'Is it too late for us to fight AI over copyright?',
            'Why is the media selling their prized content to OpenAI?',
        ],
        'tone': 'Provocative, personal, argumentative',
        'open_rate_impact': 'Variable - high engagement when done well',
    },
    
    'warning_concern': {
        'name': 'Warning / Concern',
        'icon': '⚠️',
        'description': 'Highlighting risks, dangers, or problems with AI',
        'headline_patterns': [
            '[Danger] that [consequence]',
            'The [problem] that [industry] isn\'t talking about',
            'AI will [negative outcome]',
            'Why [scary development] should worry you',
        ],
        'examples': [
            'Five ways AI can save and endanger Public Service Media',
            'AI will turn the web into a wasteland... what\'s next?',
            'ChatGPT drinks 500ml of fresh water for every 50 texts',
            'Those insane AI videos... we need to talk',
        ],
        'tone': 'Cautionary, serious, urgent',
        'open_rate_impact': 'Lower than optimistic (-7.9% for doom)',
    },
    
    'future_opportunity': {
        'name': 'Future / Opportunity',
        'icon': '🔮',
        'description': 'Looking ahead at what AI could enable',
        'headline_patterns': [
            'The future of [topic]',
            'Could [technology] transform [industry]?',
            'What [development] means for [audience]',
            '[Number] opportunities in [area]',
        ],
        'examples': [
            'How is AI going to transform education?',
            'AI could improve the criminal justice system',
            'Will Google & AI destroy podcasting?',
        ],
        'tone': 'Forward-looking, speculative, hopeful',
        'open_rate_impact': '+5% for optimism',
    },
    
    'question_exploration': {
        'name': 'Question / Exploration',
        'icon': '❓',
        'description': 'Posing and exploring a central question',
        'headline_patterns': [
            'Is [claim] true?',
            'What happens when [scenario]?',
            'Could [possibility] actually work?',
            'Will [prediction] come true?',
        ],
        'examples': [
            'Is AI funnier than we want to accept?',
            'Could a deepfake take over your life?',
            'Is more "media literacy" the answer to AI slop?',
        ],
        'tone': 'Curious, exploratory, balanced',
        'open_rate_impact': '-9% for question headlines (avoid in title)',
    },
    
    'africa_global_south': {
        'name': 'Africa / Global South Focus',
        'icon': '🌍',
        'description': 'AI developments and perspectives from Africa',
        'headline_patterns': [
            '[African topic] and AI',
            '[Number] [African] projects using AI',
            'AI in [African country/region]',
            'Lessons from [African initiative]',
        ],
        'examples': [
            'It is time to Develop AI for African media',
            '3 Incredible AI solutions for Africa',
            'Lessons in AI from Bloomberg\'s Africa Business Media Innovators',
            'The 7 African projects that are embracing AI',
        ],
        'tone': 'Empowering, localized, solution-oriented',
        'open_rate_impact': '+9.3% (second best performer)',
    },
    
    'listicle_roundup': {
        'name': 'Listicle / Roundup',
        'icon': '📋',
        'description': 'Curated list of items, tools, or developments',
        'headline_patterns': [
            '[Number] [things] that [action]',
            'The top [number] [category]',
            '[Number] ways to [goal]',
            'The best [category] of [time period]',
        ],
        'examples': [
            'AI Lawsuits - The Global Top 5',
            '3 Incredible AI solutions for Africa',
            'Five ways AI can save and endanger Public Service Media',
        ],
        'tone': 'Scannable, informative, comprehensive',
        'open_rate_impact': 'Average - good for engagement',
    },
    
    'versus_comparison': {
        'name': 'Versus / Comparison',
        'icon': '⚔️',
        'description': 'Comparing or contrasting two sides',
        'headline_patterns': [
            '[A] vs [B]',
            '[Entity] against [Entity]',
            'The battle between [X] and [Y]',
            'Who will win: [X] or [Y]?',
        ],
        'examples': [
            'The AI Wars Have Begun: Apple vs the BBC',
            'AI vs The Law - who will win?',
            'Disney v AI - the most under-reported story',
        ],
        'tone': 'Dramatic, engaging, conflict-driven',
        'open_rate_impact': 'Good for curiosity',
    },
    
    'regulation_legal': {
        'name': 'Regulation / Legal',
        'icon': '⚖️',
        'description': 'Policy, law, and regulatory developments',
        'headline_patterns': [
            'The [regulation] and what it means',
            '[Legal development] in AI',
            'New rules for [topic]',
            'What [law/act] means for [audience]',
        ],
        'examples': [
            'What is the AI EU Act backtracking on?',
            'Let\'s not dismiss the EU AI Act',
            'AI Lawsuits - The Global Top 5',
        ],
        'tone': 'Serious, informative, practical',
        'open_rate_impact': 'Average',
    },
    
    'deep_dive': {
        'name': 'Deep Dive / Analysis',
        'icon': '🔍',
        'description': 'In-depth exploration of a complex topic',
        'headline_patterns': [
            'Inside [topic]',
            'Understanding [complex issue]',
            'The complete guide to [topic]',
            'Everything you need to know about [X]',
        ],
        'examples': [
            'The insane bias in generative images',
            'AI & Data Incest - What is the Solution?',
            'Not all languages are created equal',
        ],
        'tone': 'Thorough, educational, expert',
        'open_rate_impact': 'Good for engaged readers',
    },
}


def get_story_types() -> dict:
    """Return all story type definitions."""
    return STORY_TYPES


def get_story_type_list() -> list[dict]:
    """Return story types as a list for UI display."""
    result = []
    for key, data in STORY_TYPES.items():
        result.append({
            'key': key,
            **data
        })
    return result









