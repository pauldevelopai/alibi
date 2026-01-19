"""
South African & Namibian Context Database

Specific vocabulary, objects, and scenarios for Southern African context.
This enhances AI vision understanding of regional specifics.
"""

from typing import List, Dict

# South African specific vehicles
SA_VEHICLES = {
    'minibus_taxi': {
        'description': 'Toyota Quantum or similar 14-16 seater minibus taxi',
        'keywords': ['minibus', 'taxi', 'quantum', 'kombi'],
        'context': 'Primary public transport in townships and cities'
    },
    'bakkie': {
        'description': 'Pickup truck (South African term)',
        'keywords': ['bakkie', 'pickup', 'truck'],
        'context': 'Common utility vehicle'
    },
    'delivery_vehicle': {
        'description': 'Delivery van or bakkie with company branding',
        'keywords': ['delivery', 'courier', 'branded'],
        'context': 'Online shopping delivery, courier services'
    }
}

# South African locations and architecture
SA_LOCATIONS = {
    'township': {
        'description': 'Historically disadvantaged residential area',
        'features': ['informal housing', 'RDP houses', 'close proximity', 'unpaved roads'],
        'context': 'Require sensitive, respectful terminology'
    },
    'informal_settlement': {
        'description': 'Temporary housing structures',
        'features': ['corrugated iron', 'shacks', 'informal structures'],
        'context': 'Describe factually without judgment'
    },
    'rdp_house': {
        'description': 'Government-provided housing (Reconstruction and Development Programme)',
        'features': ['small', 'uniform', 'brick', 'minimal'],
        'context': 'Common in townships'
    },
    'security_estate': {
        'description': 'Gated residential community with security',
        'features': ['boom gate', 'security guard', 'walls', 'controlled access'],
        'context': 'Common in urban South Africa'
    }
}

# Regional objects
SA_OBJECTS = {
    'braai': {
        'description': 'Barbecue grill (South African term)',
        'keywords': ['braai', 'grill', 'barbecue'],
        'context': 'Social gathering activity'
    },
    'spaza_shop': {
        'description': 'Small informal convenience store',
        'keywords': ['spaza', 'tuckshop', 'informal shop'],
        'context': 'Common in townships'
    },
    'shebeen': {
        'description': 'Informal tavern or bar',
        'keywords': ['shebeen', 'tavern', 'informal bar'],
        'context': 'Social gathering place'
    },
    'prepaid_electricity_box': {
        'description': 'Prepaid electricity meter box',
        'keywords': ['prepaid', 'electricity', 'meter box'],
        'context': 'Common in South African homes'
    }
}

# Namibian specific context
NAMIBIA_CONTEXT = {
    'wildlife': {
        'description': 'Namibian wildlife',
        'animals': ['oryx', 'springbok', 'kudu', 'elephant', 'giraffe', 'zebra', 'lion', 'leopard'],
        'context': 'May appear near settlements, roads'
    },
    'desert_environment': {
        'description': 'Namib Desert landscape',
        'features': ['sand dunes', 'arid', 'sparse vegetation', 'rocky terrain'],
        'context': 'Unique environment requiring specific description'
    },
    'skeleton_coast': {
        'description': 'Coastal area with shipwrecks',
        'features': ['coastal', 'foggy', 'windswept', 'remote'],
        'context': 'Unique Namibian geography'
    }
}

# Common activities
SA_ACTIVITIES = {
    'queueing': {
        'description': 'People standing in line/queue',
        'keywords': ['queue', 'line', 'waiting'],
        'context': 'Common at taxi ranks, shops, ATMs'
    },
    'street_vendor': {
        'description': 'Person selling goods on street',
        'keywords': ['vendor', 'hawker', 'selling', 'informal trading'],
        'context': 'Common economic activity'
    },
    'taxi_rank_activity': {
        'description': 'Activity at minibus taxi pickup point',
        'keywords': ['taxi rank', 'loading', 'passengers', 'minibus'],
        'context': 'Busy public transport hub'
    },
    'load_shedding': {
        'description': 'Scheduled power outage period',
        'keywords': ['dark', 'no lights', 'power out', 'generators'],
        'context': 'Common in South Africa, affects security'
    }
}

# Safety and security context
SA_SECURITY_CONTEXT = {
    'electric_fence': {
        'description': 'Electrified perimeter fence',
        'keywords': ['electric fence', 'perimeter', 'high voltage'],
        'context': 'Common security measure'
    },
    'armed_response': {
        'description': 'Private security response vehicle',
        'keywords': ['armed response', 'security vehicle', 'ADT', 'Fidelity'],
        'context': 'Common in residential areas'
    },
    'boom_gate': {
        'description': 'Vehicle access control barrier',
        'keywords': ['boom', 'gate', 'barrier', 'access control'],
        'context': 'Common at entrances to estates, parking'
    },
    'burglar_bars': {
        'description': 'Metal security bars on windows',
        'keywords': ['burglar bars', 'security bars', 'window bars'],
        'context': 'Standard security feature'
    }
}

# Cultural sensitivity guidelines
CULTURAL_GUIDELINES = {
    'respectful_language': [
        'Use factual, neutral descriptions',
        'Avoid stereotypes or assumptions',
        'Describe what you see, not judgments',
        'Use respectful terminology for locations',
        'Be aware of economic disparities',
        'Respect cultural diversity'
    ],
    'terminology': {
        'preferred': {
            'township': 'Use instead of "slum"',
            'informal settlement': 'Use instead of "squatter camp"',
            'informal trader': 'Use instead of "illegal vendor"',
            'pedestrian': 'Neutral term for people walking'
        },
        'avoid': [
            'slum',
            'squatter',
            'illegal (unless factual crime)',
            'suspicious (unless specific behavior)',
            'sketchy',
            'dodgy'
        ]
    }
}

# Prompt enhancement for South African context
SA_ENHANCED_PROMPT = """You are analyzing security camera footage in South Africa/Namibia.

Regional Context You Must Know:
1. VEHICLES: Minibus taxis (Toyota Quantum), bakkies (pickups), delivery vehicles
2. LOCATIONS: Townships, informal settlements, RDP houses, security estates
3. OBJECTS: Braai (BBQ), spaza shops, prepaid electricity boxes, burglar bars
4. ACTIVITIES: Queueing, street vendors, taxi ranks, load shedding effects
5. SECURITY: Electric fences, armed response, boom gates, burglar bars
6. WILDLIFE (Namibia): Oryx, springbok, kudu, elephants near settlements
7. ENVIRONMENT: Desert landscapes, arid conditions, unique architecture

Cultural Sensitivity:
- Use respectful, factual language
- Describe what you see without judgment
- Use correct regional terminology
- Be aware of economic and social context
- Avoid stereotypes

Describe what you see accurately and contextually."""


def enhance_prompt_for_sa_context(base_prompt: str) -> str:
    """Add South African context to any base prompt"""
    return f"{SA_ENHANCED_PROMPT}\n\n{base_prompt}"


def get_context_hints(description: str) -> List[str]:
    """
    Analyze description and provide context hints.
    
    Helps users understand if AI missed regional context.
    """
    hints = []
    
    desc_lower = description.lower()
    
    # Check for vehicles
    if 'minibus' in desc_lower or 'taxi' in desc_lower:
        hints.append('🚐 Minibus taxi - primary public transport in SA')
    
    if 'bakkie' in desc_lower or 'pickup' in desc_lower:
        hints.append('🚙 Bakkie - South African term for pickup truck')
    
    # Check for locations
    if 'township' in desc_lower or 'informal' in desc_lower:
        hints.append('🏘️ Township/informal settlement - use respectful terminology')
    
    # Check for security features
    if 'fence' in desc_lower or 'security' in desc_lower:
        hints.append('🔒 Security features common in SA (electric fences, bars, etc.)')
    
    # Check for activities
    if 'queue' in desc_lower or 'line' in desc_lower:
        hints.append('👥 Queueing - common at taxi ranks, shops, ATMs')
    
    if 'vendor' in desc_lower or 'selling' in desc_lower:
        hints.append('🛒 Street vendor/informal trader - common economic activity')
    
    return hints


# Export for use in vision analyzer
__all__ = [
    'SA_VEHICLES',
    'SA_LOCATIONS',
    'SA_OBJECTS',
    'NAMIBIA_CONTEXT',
    'SA_ACTIVITIES',
    'SA_SECURITY_CONTEXT',
    'CULTURAL_GUIDELINES',
    'SA_ENHANCED_PROMPT',
    'enhance_prompt_for_sa_context',
    'get_context_hints'
]
