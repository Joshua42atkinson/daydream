# vocabulary.py - Handles SAT/AWL vocabulary checking and XP calculation for Daydream

import re

# --- AWL Data (Headwords mapped to Sublist Number 1-10) ---
# Source: Based on common versions of Coxhead's Academic Word List headwords.
# Note: This is embedded for simplicity; could be loaded from a file.
AWL_WORDS = {
    # Sublist 1
    'analyse': 1, 'approach': 1, 'area': 1, 'assess': 1, 'assume': 1, 'authority': 1, 'available': 1,
    'benefit': 1, 'concept': 1, 'consist': 1, 'constitute': 1, 'context': 1, 'contract': 1, 'create': 1,
    'data': 1, 'define': 1, 'derive': 1, 'distribute': 1, 'economy': 1, 'environment': 1, 'establish': 1,
    'estimate': 1, 'evident': 1, 'export': 1, 'factor': 1, 'finance': 1, 'formula': 1, 'function': 1,
    'identify': 1, 'income': 1, 'indicate': 1, 'individual': 1, 'interpret': 1, 'involve': 1, 'issue': 1,
    'labour': 1, 'legal': 1, 'legislate': 1, 'major': 1, 'method': 1, 'occur': 1, 'percent': 1, 'period': 1,
    'policy': 1, 'principle': 1, 'proceed': 1, 'process': 1, 'require': 1, 'research': 1, 'respond': 1,
    'role': 1, 'section': 1, 'sector': 1, 'significant': 1, 'similar': 1, 'source': 1, 'specific': 1,
    'structure': 1, 'theory': 1, 'vary': 1,
    # Sublist 2
    'achieve': 2, 'acquire': 2, 'administrate': 2, 'affect': 2, 'appropriate': 2, 'aspect': 2, 'assist': 2,
    'category': 2, 'chapter': 2, 'commission': 2, 'community': 2, 'complex': 2, 'compute': 2, 'conclude': 2,
    'conduct': 2, 'consequent': 2, 'construct': 2, 'consume': 2, 'credit': 2, 'culture': 2, 'design': 2,
    'distinct': 2, 'element': 2, 'equate': 2, 'evaluate': 2, 'feature': 2, 'final': 2, 'focus': 2,
    'impact': 2, 'injure': 2, 'institute': 2, 'invest': 2, 'item': 2, 'journal': 2, 'maintain': 2,
    'normal': 2, 'obtain': 2, 'participate': 2, 'perceive': 2, 'positive': 2, 'potential': 2, 'previous': 2,
    'primary': 2, 'purchase': 2, 'range': 2, 'region': 2, 'regulate': 2, 'relevant': 2, 'reside': 2,
    'resource': 2, 'restrict': 2, 'secure': 2, 'seek': 2, 'select': 2, 'site': 2, 'strategy': 2,
    'survey': 2, 'text': 2, 'tradition': 2, 'transfer': 2,
    # Sublist 3
    'alternative': 3, 'circumstance': 3, 'comment': 3, 'compensate': 3, 'component': 3, 'consent': 3,
    'considerable': 3, 'constant': 3, 'constrain': 3, 'contribute': 3, 'convene': 3, 'coordinate': 3,
    'core': 3, 'corporate': 3, 'correspond': 3, 'criteria': 3, 'deduce': 3, 'demonstrate': 3, 'document': 3,
    'dominate': 3, 'emphasis': 3, 'ensure': 3, 'exclude': 3, 'framework': 3, 'fund': 3, 'illustrate': 3,
    'immigrate': 3, 'imply': 3, 'initial': 3, 'instance': 3, 'interact': 3, 'justify': 3, 'layer': 3,
    'link': 3, 'locate': 3, 'maximise': 3, 'minor': 3, 'negate': 3, 'outcome': 3, 'partner': 3,
    'philosophy': 3, 'physical': 3, 'proportion': 3, 'publish': 3, 'react': 3, 'register': 3, 'rely': 3,
    'remove': 3, 'scheme': 3, 'sequence': 3, 'sex': 3, 'shift': 3, 'specify': 3, 'sufficient': 3,
    'task': 3, 'technical': 3, 'technique': 3, 'technology': 3, 'valid': 3, 'volume': 3,
    # Sublist 4
    'access': 4, 'adequate': 4, 'annual': 4, 'apparent': 4, 'approximate': 4, 'attitude': 4, 'attribute': 4,
    'civil': 4, 'code': 4, 'commit': 4, 'communicate': 4, 'concentrate': 4, 'confer': 4, 'contrast': 4,
    'cycle': 4, 'debate': 4, 'despite': 4, 'dimension': 4, 'domestic': 4, 'emerge': 4, 'error': 4,
    'ethnic': 4, 'goal': 4, 'grant': 4, 'hence': 4, 'hypothesis': 4, 'implement': 4, 'implicate': 4,
    'impose': 4, 'integrate': 4, 'internal': 4, 'investigate': 4, 'job': 4, 'label': 4, 'mechanism': 4,
    'obvious': 4, 'occupy': 4, 'option': 4, 'output': 4, 'overall': 4, 'parallel': 4, 'parameter': 4,
    'phase': 4, 'predict': 4, 'principal': 4, 'prior': 4, 'professional': 4, 'project': 4, 'promote': 4,
    'regime': 4, 'resolve': 4, 'retain': 4, 'series': 4, 'statistic': 4, 'status': 4, 'stress': 4,
    'subsequent': 4, 'sum': 4, 'summary': 4, 'undertake': 4,
    # Sublist 5
    'academy': 5, 'adjust': 5, 'alter': 5, 'amend': 5, 'aware': 5, 'capacity': 5, 'challenge': 5,
    'clause': 5, 'compound': 5, 'conflict': 5, 'consult': 5, 'contact': 5, 'decline': 5, 'discrete': 5,
    'draft': 5, 'enable': 5, 'energy': 5, 'enforce': 5, 'entity': 5, 'equivalent': 5, 'evolve': 5,
    'expand': 5, 'expose': 5, 'external': 5, 'facilitate': 5, 'fundamental': 5, 'generate': 5,
    'generation': 5, 'image': 5, 'liberal': 5, 'licence': 5, 'logic': 5, 'margin': 5, 'medical': 5,
    'mental': 5, 'modify': 5, 'monitor': 5, 'network': 5, 'notion': 5, 'objective': 5, 'orient': 5,
    'perspective': 5, 'precise': 5, 'prime': 5, 'psychology': 5, 'pursue': 5, 'ratio': 5, 'reject': 5,
    'revenue': 5, 'stable': 5, 'style': 5, 'substitute': 5, 'sustain': 5, 'symbol': 5, 'target': 5,
    'transit': 5, 'trend': 5, 'version': 5, 'welfare': 5, 'whereas': 5,
    # Sublist 6
    'abstract': 6, 'accurate': 6, 'acknowledge': 6, 'aggregate': 6, 'allocate': 6, 'assign': 6, 'attach': 6,
    'author': 6, 'bond': 6, 'brief': 6, 'capable': 6, 'cite': 6, 'cooperate': 6, 'discriminate': 6,
    'display': 6, 'diverse': 6, 'domain': 6, 'edit': 6, 'enhance': 6, 'estate': 6, 'exceed': 6,
    'expert': 6, 'explicit': 6, 'federal': 6, 'fee': 6, 'flexible': 6, 'furthermore': 6, 'gender': 6,
    'ignore': 6, 'incentive': 6, 'incidence': 6, 'incorporate': 6, 'index': 6, 'inhibit': 6, 'initiate': 6,
    'input': 6, 'instruct': 6, 'intelligent': 6, 'interval': 6, 'lecture': 6, 'migrate': 6, 'minimum': 6,
    'ministry': 6, 'motive': 6, 'neutral': 6, 'nevertheless': 6, 'overseas': 6, 'precede': 6, 'presume': 6,
    'rational': 6, 'recover': 6, 'reveal': 6, 'scope': 6, 'subsidy': 6, 'tape': 6, 'trace': 6,
    'transform': 6, 'transport': 6, 'underlie': 6, 'utilise': 6,
    # Sublist 7
    'adapt': 7, 'adult': 7, 'advocate': 7, 'aid': 7, 'channel': 7, 'chemical': 7, 'classic': 7,
    'comprehensive': 7, 'comprise': 7, 'confirm': 7, 'contrary': 7, 'convert': 7, 'couple': 7, 'decade': 7,
    'definite': 7, 'deny': 7, 'differentiate': 7, 'dispose': 7, 'dynamic': 7, 'eliminate': 7, 'empirical': 7,
    'equip': 7, 'extract': 7, 'file': 7, 'finite': 7, 'foundation': 7, 'globe': 7, 'grade': 7,
    'guarantee': 7, 'hierarchical': 7, 'identical': 7, 'ideology': 7, 'infer': 7, 'innovate': 7, 'insert': 7,
    'intervene': 7, 'isolate': 7, 'media': 7, 'mode': 7, 'paradigm': 7, 'phenomenon': 7, 'priority': 7,
    'prohibit': 7, 'publication': 7, 'quote': 7, 'release': 7, 'reverse': 7, 'simulate': 7, 'sole': 7,
    'somewhat': 7, 'submit': 7, 'successor': 7, 'survive': 7, 'thesis': 7, 'topic': 7, 'transmit': 7,
    'ultimate': 7, 'unique': 7, 'visible': 7, 'voluntary': 7,
    # Sublist 8
    'abandon': 8, 'accompany': 8, 'accumulate': 8, 'ambiguous': 8, 'append': 8, 'appreciate': 8,
    'arbitrary': 8, 'automate': 8, 'bias': 8, 'chart': 8, 'clarify': 8, 'commodity': 8, 'complement': 8,
    'conform': 8, 'contemporary': 8, 'contradict': 8, 'crucial': 8, 'currency': 8, 'denote': 8, 'detect': 8,
    'deviate': 8, 'displace': 8, 'drama': 8, 'eventual': 8, 'exhibit': 8, 'exploit': 8, 'fluctuate': 8,
    'guideline': 8, 'highlight': 8, 'implicit': 8, 'induce': 8, 'inevitable': 8, 'infrastructure': 8,
    'inspect': 8, 'intense': 8, 'manipulate': 8, 'minimise': 8, 'nuclear': 8, 'offset': 8, 'paragraph': 8,
    'plus': 8, 'practitioner': 8, 'predominant': 8, 'prospect': 8, 'radical': 8, 'random': 8, 'reinforce': 8,
    'restore': 8, 'revise': 8, 'schedule': 8, 'tense': 8, 'terminate': 8, 'theme': 8, 'thereby': 8,
    'uniform': 8, 'vehicle': 8, 'via': 8, 'virtual': 8, 'visual': 8, 'widespread': 8,
    # Sublist 9
    'accommodate': 9, 'analogy': 9, 'anticipate': 9, 'assure': 9, 'attain': 9, 'behalf': 9, 'bulk': 9,
    'cease': 9, 'coherent': 9, 'coincide': 9, 'commence': 9, 'compatible': 9, 'concurrent': 9, 'confine': 9,
    'controversy': 9, 'converse': 9, 'device': 9, 'devote': 9, 'diminish': 9, 'distort': 9, 'duration': 9,
    'erode': 9, 'ethic': 9, 'format': 9, 'found': 9, 'inherent': 9, 'insight': 9, 'integral': 9,
    'intermediate': 9, 'manual': 9, 'mature': 9, 'mediate': 9, 'medium': 9, 'military': 9, 'minimal': 9,
    'mutual': 9, 'norm': 9, 'overlap': 9, 'passive': 9, 'portion': 9, 'preliminary': 9, 'protocol': 9,
    'qualitative': 9, 'refine': 9, 'relax': 9, 'restrain': 9, 'revolution': 9, 'rigid': 9, 'route': 9,
    'scenario': 9, 'sphere': 9, 'subordinate': 9, 'supplement': 9, 'suspend': 9, 'team': 9, 'temporary': 9,
    'trigger': 9, 'unify': 9, 'violate': 9, 'vision': 9,
    # Sublist 10
    'adjacent': 10, 'albeit': 10, 'assemble': 10, 'collapse': 10, 'colleague': 10, 'compile': 10,
    'conceive': 10, 'convince': 10, 'depress': 10, 'encounter': 10, 'enormous': 10, 'forthcoming': 10,
    'incline': 10, 'integrity': 10, 'intrinsic': 10, 'invoke': 10, 'levy': 10, 'likewise': 10,
    'nonetheless': 10, 'notwithstanding': 10, 'odd': 10, 'ongoing': 10, 'panel': 10, 'persist': 10,
    'pose': 10, 'reluctance': 10, 'so-called': 10, 'straightforward': 10, 'undergo': 10, 'whereby': 10
}

# --- XP and Category Configuration ---
XP_TIERS = {
    'common': 3,      # XP for common AWL words
    'medium': 5,      # XP for medium AWL words
    'challenging': 10 # XP for challenging AWL words
}

# Map AWL sublists to our categories
# Adjust mapping as needed based on desired difficulty spread
SUBLIST_TO_CATEGORY = {
    1: 'common', 2: 'common', 3: 'common',
    4: 'medium', 5: 'medium', 6: 'medium', 7: 'medium',
    8: 'challenging', 9: 'challenging', 10: 'challenging'
}

# Pre-calculate category for each word for faster lookup
AWL_CATEGORIZED = {word: SUBLIST_TO_CATEGORY.get(sublist, 'medium') # Default to medium if sublist missing?
                   for word, sublist in AWL_WORDS.items()}

# --- Main XP Calculation Function ---

def calculate_xp(player_input_text: str, learned_vocab_set: set) -> tuple[int, set]:
    """
    Calculates XP based on finding NEW AWL words in player input, using tiered XP.

    Args:
        player_input_text: The raw text input from the player.
        learned_vocab_set: A set of words the player has already learned (and received XP for).

    Returns:
        A tuple containing:
        - total_xp_gain (int): The amount of XP earned from this input.
        - found_new_awl_words (set): A set of the new AWL words found in this input.
    """
    if not player_input_text:
        return 0, set()

    total_xp_gain = 0
    found_new_awl_words = set()

    # 1. Clean and tokenize the input text
    # Convert to lowercase, remove basic punctuation, split into words
    text_lower = player_input_text.lower()
    # Remove punctuation that might interfere with word matching
    text_cleaned = re.sub(r'[^\w\s-]', '', text_lower) # Keep hyphens within words
    words = text_cleaned.split()

    # Use a set for efficient checking of unique words within this input
    unique_words_in_input = set(words)

    # 2. Check each unique word against the categorized AWL
    for word in unique_words_in_input:
        # Check if the word is in our categorized AWL list
        if word in AWL_CATEGORIZED:
            # Check if the player has *already learned* this word
            if word not in learned_vocab_set:
                # It's a new AWL word for this player! Award XP based on category.
                category = AWL_CATEGORIZED[word]
                xp_award = XP_TIERS.get(category, 0) # Get XP for the category, default 0 if somehow missing

                if xp_award > 0:
                    total_xp_gain += xp_award
                    found_new_awl_words.add(word)
                    # Optional: Print debug message
                    # print(f"[DEBUG Vocab] Found new AWL word: '{word}' (Category: {category}, XP: +{xp_award})")

    # 3. Return total XP gain and the set of new words found
    return total_xp_gain, found_new_awl_words

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    # Simulate player input and learned words
    test_input_1 = "I need to analyse the data and evaluate the subsequent impact."
    test_input_2 = "The contrast was obvious, despite the ambiguous visual presentation."
    test_input_3 = "Let's COMMENCE the project and allocate resources." # Test case insensitivity
    test_input_4 = "Look around." # No AWL words expected
    test_input_5 = "approach evaluate" # Test finding already learned words

    learned_words = set()
    print(f"Input: \"{test_input_1}\"")
    xp1, new1 = calculate_xp(test_input_1, learned_words)
    print(f"XP Gained: {xp1}, New Words: {new1}")
    learned_words.update(new1)
    print(f"Learned List: {learned_words}\n")

    print(f"Input: \"{test_input_2}\"")
    xp2, new2 = calculate_xp(test_input_2, learned_words)
    print(f"XP Gained: {xp2}, New Words: {new2}")
    learned_words.update(new2)
    print(f"Learned List: {learned_words}\n")

    print(f"Input: \"{test_input_3}\"")
    xp3, new3 = calculate_xp(test_input_3, learned_words)
    print(f"XP Gained: {xp3}, New Words: {new3}")
    learned_words.update(new3)
    print(f"Learned List: {learned_words}\n")

    print(f"Input: \"{test_input_4}\"")
    xp4, new4 = calculate_xp(test_input_4, learned_words)
    print(f"XP Gained: {xp4}, New Words: {new4}")
    learned_words.update(new4)
    print(f"Learned List: {learned_words}\n")

    print(f"Input: \"{test_input_5}\"")
    xp5, new5 = calculate_xp(test_input_5, learned_words)
    print(f"XP Gained: {xp5}, New Words: {new5}")
    learned_words.update(new5)
    print(f"Learned List: {learned_words}\n")