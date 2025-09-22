"""
University Selection Algorithm for Scholarport.

This module implements the intelligent algorithm to select exactly 3 universities
from our 243-university dataset based on student preferences and requirements.
"""

import re
import random
from typing import Dict, List, Optional, Tuple
from chat.models import University, ConversationSession


class UniversitySelector:
    """
    Intelligent university selection algorithm.

    Always returns exactly 3 universities that best match student preferences:
    - Country preference
    - Budget compatibility
    - Test score requirements
    - Program availability
    - Ranking and quality
    """

    def __init__(self):
        """Initialize the selector"""
        pass

    def select_universities(self, conversation: ConversationSession) -> List[Dict]:
        """
        Select exactly 3 universities based on conversation data.

        Args:
            conversation: Completed conversation session

        Returns:
            List of 3 university dictionaries
        """
        # Extract student preferences
        preferences = self._extract_preferences(conversation)

        # Get all universities
        universities = University.objects.all()

        # Apply filters
        filtered_universities = self._apply_filters(universities, preferences)

        # Score and rank universities
        scored_universities = self._score_universities(filtered_universities, preferences)

        # Select top 3 with diversity
        selected_3 = self._select_diverse_top_3(scored_universities, preferences)

        # Convert to response format
        return self._format_university_response(selected_3, preferences)

    def _extract_preferences(self, conversation: ConversationSession) -> Dict:
        """
        Extract and parse student preferences from conversation.

        Args:
            conversation: The conversation session

        Returns:
            Dictionary of structured preferences
        """
        # Parse budget
        budget_text = conversation.processed_budget or conversation.budget_response or ""
        budget_info = self._parse_budget(budget_text)

        # Parse test score
        test_text = conversation.processed_test_score or conversation.test_score_response or ""
        test_info = self._parse_test_score(test_text)

        # Parse country
        country_text = conversation.processed_country or conversation.country_response or ""
        country = self._parse_country(country_text)

        # Parse education
        education_text = conversation.processed_education or conversation.education_response or ""

        return {
            'name': conversation.processed_name or conversation.name_response or "Student",
            'education': education_text,
            'budget_amount': budget_info['amount'],
            'budget_currency': budget_info['currency'],
            'test_type': test_info['type'],
            'test_score': test_info['score'],
            'country': country,
            'education_level': self._determine_education_level(education_text)
        }

    def _parse_budget(self, budget_text: str) -> Dict:
        """Parse budget text into amount and currency"""
        if not budget_text:
            return {'amount': 25000, 'currency': 'USD'}  # Default

        # Extract amount
        amount_match = re.search(r'(\d+(?:,\d+)*)', budget_text.replace(',', ''))
        amount = int(amount_match.group(1)) if amount_match else 25000

        # Extract currency
        currency = 'USD'  # Default
        if '£' in budget_text or 'GBP' in budget_text.upper() or 'pound' in budget_text.lower():
            currency = 'GBP'
        elif '€' in budget_text or 'EUR' in budget_text.upper() or 'euro' in budget_text.lower():
            currency = 'EUR'
        elif 'CAD' in budget_text.upper() or 'canadian' in budget_text.lower():
            currency = 'CAD'
        elif 'AUD' in budget_text.upper() or 'australian' in budget_text.lower():
            currency = 'AUD'
        elif 'SGD' in budget_text.upper() or 'singapore' in budget_text.lower():
            currency = 'SGD'
        elif 'CHF' in budget_text.upper() or 'swiss' in budget_text.lower():
            currency = 'CHF'

        return {'amount': amount, 'currency': currency}

    def _parse_test_score(self, test_text: str) -> Dict:
        """Parse test score text into type and score"""
        if not test_text:
            return {'type': 'IELTS', 'score': 6.0}  # Default

        test_text_upper = test_text.upper()

        if 'IELTS' in test_text_upper:
            # Extract IELTS score
            score_match = re.search(r'(\d+(?:\.\d+)?)', test_text)
            score = float(score_match.group(1)) if score_match else 6.0
            return {'type': 'IELTS', 'score': score}
        elif 'TOEFL' in test_text_upper:
            # Extract TOEFL score
            score_match = re.search(r'(\d+)', test_text)
            score = int(score_match.group(1)) if score_match else 80
            return {'type': 'TOEFL', 'score': score}
        else:
            # Try to guess from numbers
            score_match = re.search(r'(\d+(?:\.\d+)?)', test_text)
            if score_match:
                score_val = float(score_match.group(1))
                if score_val <= 9:  # Likely IELTS
                    return {'type': 'IELTS', 'score': score_val}
                else:  # Likely TOEFL
                    return {'type': 'TOEFL', 'score': int(score_val)}

        return {'type': 'IELTS', 'score': 6.0}  # Default

    def _parse_country(self, country_text: str) -> str:
        """Parse and standardize country name"""
        if not country_text:
            return 'USA'  # Default

        country_mapping = {
            'USA': ['usa', 'america', 'united states', 'us'],
            'UK': ['uk', 'britain', 'united kingdom', 'england', 'britain'],
            'Canada': ['canada', 'canadian'],
            'Australia': ['australia', 'aussie', 'oz'],
            'Germany': ['germany', 'german'],
            'Singapore': ['singapore'],
            'Switzerland': ['switzerland', 'swiss'],
            'France': ['france', 'french'],
            'Netherlands': ['netherlands', 'holland', 'dutch'],
        }

        country_lower = country_text.lower()
        for standard_name, variations in country_mapping.items():
            if any(var in country_lower for var in variations):
                return standard_name

        return country_text.title()  # Return as-is if not found

    def _determine_education_level(self, education_text: str) -> str:
        """Determine education level from text"""
        if not education_text:
            return 'Bachelor'

        education_lower = education_text.lower()

        if any(word in education_lower for word in ['high school', 'secondary', '12th', 'a-level']):
            return 'High School'
        elif any(word in education_lower for word in ['bachelor', 'bba', 'bsc', 'ba', 'bs', 'undergraduate']):
            return 'Bachelor'
        elif any(word in education_lower for word in ['master', 'mba', 'msc', 'ma', 'ms', 'postgraduate']):
            return 'Master'
        elif any(word in education_lower for word in ['phd', 'doctorate', 'doctoral']):
            return 'PhD'

        return 'Bachelor'  # Default

    def _apply_filters(self, universities, preferences: Dict) -> List[University]:
        """Apply basic filters to narrow down universities"""
        filtered = []

        for uni in universities:
            # Country filter (most important)
            if not self._matches_country(uni, preferences['country']):
                continue

            # Budget filter (with tolerance)
            if not self._matches_budget(uni, preferences['budget_amount'], preferences['budget_currency']):
                continue

            # Test score filter (if requirements exist)
            if not self._meets_test_requirements(uni, preferences['test_type'], preferences['test_score']):
                continue

            filtered.append(uni)

        return filtered

    def _matches_country(self, university: University, preferred_country: str) -> bool:
        """Check if university is in preferred country"""
        uni_country = university.country.strip()

        # Direct match
        if uni_country.lower() == preferred_country.lower():
            return True

        # Handle common variations
        country_variations = {
            'USA': ['United States', 'US', 'America'],
            'UK': ['United Kingdom', 'Britain', 'England'],
            'UAE': ['United Arab Emirates'],
            'Singapore': ['Republic of Singapore']
        }

        for standard, variations in country_variations.items():
            if preferred_country == standard and uni_country in variations:
                return True
            if uni_country == standard and preferred_country in variations:
                return True

        return False

    def _matches_budget(self, university: University, budget_amount: int, budget_currency: str) -> bool:
        """Check if university tuition fits within budget (with 20% tolerance)"""
        try:
            # Extract tuition amount and currency
            tuition_match = re.search(r'(\d+(?:,\d+)*)\s*([A-Z]{3})', university.tuition)
            if not tuition_match:
                return True  # If we can't parse tuition, include it

            tuition_amount = int(tuition_match.group(1).replace(',', ''))
            tuition_currency = tuition_match.group(2)

            # Convert to common currency (USD) for comparison
            conversion_rates = {
                'USD': 1.0,
                'GBP': 1.27,  # 1 GBP = 1.27 USD
                'EUR': 1.08,  # 1 EUR = 1.08 USD
                'CAD': 0.74,  # 1 CAD = 0.74 USD
                'AUD': 0.65,  # 1 AUD = 0.65 USD
                'SGD': 0.74,  # 1 SGD = 0.74 USD
                'CHF': 1.09,  # 1 CHF = 1.09 USD
            }

            # Convert both to USD
            budget_usd = budget_amount * conversion_rates.get(budget_currency, 1.0)
            tuition_usd = tuition_amount * conversion_rates.get(tuition_currency, 1.0)

            # Allow 25% tolerance above budget
            return tuition_usd <= budget_usd * 1.25

        except (ValueError, AttributeError):
            return True  # If parsing fails, include the university

    def _meets_test_requirements(self, university: University, test_type: str, test_score: float) -> bool:
        """Check if student meets university test requirements"""
        try:
            if test_type.upper() == 'IELTS' and university.ielts_requirement:
                return test_score >= university.ielts_requirement - 0.5  # 0.5 tolerance
            elif test_type.upper() == 'TOEFL' and university.toefl_requirement:
                return test_score >= university.toefl_requirement - 5  # 5 point tolerance
        except (ValueError, TypeError):
            pass

        return True  # If no requirements or parsing issues, include the university

    def _score_universities(self, universities: List[University], preferences: Dict) -> List[Tuple[University, float]]:
        """Score universities based on multiple factors"""
        scored = []

        for uni in universities:
            score = 0.0

            # Budget score (30% weight) - prefer universities within budget
            budget_score = self._calculate_budget_score(uni, preferences['budget_amount'], preferences['budget_currency'])
            score += budget_score * 0.3

            # Test score match (25% weight) - prefer universities student can get into
            test_score = self._calculate_test_score(uni, preferences['test_type'], preferences['test_score'])
            score += test_score * 0.25

            # Ranking score (20% weight) - prefer higher ranked universities
            ranking_score = self._calculate_ranking_score(uni)
            score += ranking_score * 0.2

            # Program relevance (15% weight) - prefer universities with relevant programs
            program_score = self._calculate_program_score(uni, preferences['education'])
            score += program_score * 0.15

            # Affordability bonus (10% weight) - bonus for "affordable" universities
            affordability_score = self._calculate_affordability_score(uni)
            score += affordability_score * 0.1

            scored.append((uni, score))

        return sorted(scored, key=lambda x: x[1], reverse=True)

    def _calculate_budget_score(self, university: University, budget_amount: int, budget_currency: str) -> float:
        """Calculate budget compatibility score (0-1)"""
        try:
            tuition_match = re.search(r'(\d+(?:,\d+)*)\s*([A-Z]{3})', university.tuition)
            if not tuition_match:
                return 0.5  # Neutral if can't parse

            tuition_amount = int(tuition_match.group(1).replace(',', ''))
            tuition_currency = tuition_match.group(2)

            # Convert to USD for comparison
            conversion_rates = {'USD': 1.0, 'GBP': 1.27, 'EUR': 1.08, 'CAD': 0.74, 'AUD': 0.65, 'SGD': 0.74, 'CHF': 1.09}

            budget_usd = budget_amount * conversion_rates.get(budget_currency, 1.0)
            tuition_usd = tuition_amount * conversion_rates.get(tuition_currency, 1.0)

            # Score based on how well tuition fits in budget
            ratio = tuition_usd / budget_usd
            if ratio <= 0.8:  # Well within budget
                return 1.0
            elif ratio <= 1.0:  # Exactly in budget
                return 0.8
            elif ratio <= 1.2:  # Slightly over budget
                return 0.5
            else:  # Way over budget
                return 0.1

        except (ValueError, AttributeError):
            return 0.5

    def _calculate_test_score(self, university: University, test_type: str, test_score: float) -> float:
        """Calculate test score compatibility (0-1)"""
        try:
            if test_type.upper() == 'IELTS' and university.ielts_requirement:
                if test_score >= university.ielts_requirement:
                    return 1.0  # Meets requirement
                elif test_score >= university.ielts_requirement - 0.5:
                    return 0.7  # Close to requirement
                else:
                    return 0.2  # Below requirement
            elif test_type.upper() == 'TOEFL' and university.toefl_requirement:
                if test_score >= university.toefl_requirement:
                    return 1.0
                elif test_score >= university.toefl_requirement - 10:
                    return 0.7
                else:
                    return 0.2
        except (ValueError, TypeError):
            pass

        return 0.8  # Default if no requirements

    def _calculate_ranking_score(self, university: University) -> float:
        """Calculate ranking score (0-1)"""
        try:
            ranking = university.ranking
            if ranking == '1':
                return 1.0
            elif '-' in ranking:  # Range like "10-20"
                start = int(ranking.split('-')[0])
                if start <= 10:
                    return 0.9
                elif start <= 50:
                    return 0.8
                elif start <= 100:
                    return 0.7
                elif start <= 200:
                    return 0.6
                else:
                    return 0.5
            else:
                rank_num = int(ranking)
                if rank_num <= 10:
                    return 0.95
                elif rank_num <= 50:
                    return 0.85
                elif rank_num <= 100:
                    return 0.75
                else:
                    return 0.6
        except (ValueError, AttributeError):
            return 0.6  # Default for unranked

    def _calculate_program_score(self, university: University, education_background: str) -> float:
        """Calculate program relevance score (0-1)"""
        if not education_background:
            return 0.5

        education_lower = education_background.lower()
        programs = [p.lower() for p in university.programs] if university.programs else []

        # Check for direct matches
        relevant_keywords = {
            'business': ['business', 'management', 'mba', 'finance', 'marketing'],
            'engineering': ['engineering', 'technology', 'computer', 'it', 'software'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'mathematics'],
            'arts': ['arts', 'humanities', 'literature', 'history', 'philosophy'],
            'medicine': ['medicine', 'medical', 'health', 'nursing', 'pharmacy']
        }

        for category, keywords in relevant_keywords.items():
            if any(keyword in education_lower for keyword in keywords):
                if any(keyword in ' '.join(programs) for keyword in keywords):
                    return 0.9  # High relevance
                elif category in ' '.join(programs):
                    return 0.7  # Medium relevance

        return 0.5  # Neutral if no clear match

    def _calculate_affordability_score(self, university: University) -> float:
        """Calculate affordability bonus score (0-1)"""
        affordability = university.affordability.lower() if university.affordability else ''

        if 'very affordable' in affordability:
            return 1.0
        elif 'affordable' in affordability or 'moderate' in affordability:
            return 0.8
        elif 'expensive' in affordability:
            return 0.4
        elif 'very expensive' in affordability:
            return 0.2

        return 0.6  # Default

    def _select_diverse_top_3(self, scored_universities: List[Tuple[University, float]], preferences: Dict) -> List[University]:
        """Select top 3 universities ensuring diversity"""
        if len(scored_universities) <= 3:
            return [uni for uni, score in scored_universities]

        selected = []
        budget_amount = preferences['budget_amount']

        # Get currency conversion rate
        conversion_rates = {'USD': 1.0, 'GBP': 1.27, 'EUR': 1.08, 'CAD': 0.74, 'AUD': 0.65, 'SGD': 0.74, 'CHF': 1.09}
        budget_usd = budget_amount * conversion_rates.get(preferences['budget_currency'], 1.0)

        # Categorize by budget ranges
        high_end = []    # Top 25% of budget
        mid_range = []   # Middle 50% of budget
        budget_friendly = []  # Bottom 25% of budget

        for uni, score in scored_universities:
            try:
                tuition_match = re.search(r'(\d+(?:,\d+)*)\s*([A-Z]{3})', uni.tuition)
                if tuition_match:
                    tuition_amount = int(tuition_match.group(1).replace(',', ''))
                    tuition_currency = tuition_match.group(2)
                    tuition_usd = tuition_amount * conversion_rates.get(tuition_currency, 1.0)

                    if tuition_usd >= budget_usd * 0.9:  # 90%+ of budget
                        high_end.append((uni, score))
                    elif tuition_usd >= budget_usd * 0.6:  # 60-90% of budget
                        mid_range.append((uni, score))
                    else:  # Below 60% of budget
                        budget_friendly.append((uni, score))
                else:
                    mid_range.append((uni, score))  # Default to mid-range
            except:
                mid_range.append((uni, score))

        # Select one from each category if possible
        if high_end:
            selected.append(high_end[0][0])
        if mid_range:
            selected.append(mid_range[0][0])
        if budget_friendly:
            selected.append(budget_friendly[0][0])

        # Fill remaining slots with top-scored universities
        while len(selected) < 3 and len(scored_universities) > len(selected):
            for uni, score in scored_universities:
                if uni not in selected:
                    selected.append(uni)
                    break

        return selected

    def _format_university_response(self, universities: List[University], preferences: Dict) -> List[Dict]:
        """Format universities for API response"""
        response = []

        for uni in universities:
            # Calculate why this university was selected
            why_selected = self._generate_selection_reason(uni, preferences)

            response.append({
                'name': uni.university_name,
                'country': uni.country,
                'city': uni.city,
                'tuition': uni.tuition,
                'programs': uni.programs[:3] if uni.programs else [],  # Limit to 3 programs
                'ielts_requirement': uni.ielts_requirement,
                'toefl_requirement': uni.toefl_requirement,
                'ranking': uni.ranking,
                'notes': uni.notes,
                'affordability': uni.affordability,
                'why_selected': why_selected,
                'region': uni.region
            })

        return response

    def _generate_selection_reason(self, university: University, preferences: Dict) -> str:
        """Generate a reason why this university was selected"""
        reasons = []

        # Budget reason
        try:
            tuition_match = re.search(r'(\d+(?:,\d+)*)\s*([A-Z]{3})', university.tuition)
            if tuition_match:
                tuition_amount = int(tuition_match.group(1).replace(',', ''))
                conversion_rates = {'USD': 1.0, 'GBP': 1.27, 'EUR': 1.08, 'CAD': 0.74, 'AUD': 0.65, 'SGD': 0.74, 'CHF': 1.09}
                budget_usd = preferences['budget_amount'] * conversion_rates.get(preferences['budget_currency'], 1.0)
                tuition_usd = tuition_amount * conversion_rates.get(tuition_match.group(2), 1.0)

                if tuition_usd <= budget_usd * 0.8:
                    reasons.append("Well within your budget")
                elif tuition_usd <= budget_usd:
                    reasons.append("Perfect budget match")
                else:
                    reasons.append("Great value for money")
        except:
            pass

        # Test score reason
        test_type = preferences['test_type']
        test_score = preferences['test_score']

        if test_type == 'IELTS' and university.ielts_requirement:
            if test_score >= university.ielts_requirement:
                reasons.append(f"Your IELTS {test_score} meets their requirement")
        elif test_type == 'TOEFL' and university.toefl_requirement:
            if test_score >= university.toefl_requirement:
                reasons.append(f"Your TOEFL {test_score} meets their requirement")

        # Program relevance
        if university.programs and preferences['education']:
            education_lower = preferences['education'].lower()
            programs_lower = [p.lower() for p in university.programs]

            if any('business' in education_lower and 'business' in p for p in programs_lower):
                reasons.append("Strong business programs")
            elif any('engineering' in education_lower and ('engineering' in p or 'technology' in p) for p in programs_lower):
                reasons.append("Excellent engineering programs")
            elif any('computer' in education_lower and ('computer' in p or 'it' in p) for p in programs_lower):
                reasons.append("Top computer science programs")

        # Ranking bonus
        try:
            if university.ranking and (university.ranking.isdigit() and int(university.ranking) <= 100):
                reasons.append("Highly ranked university")
            elif '-' in university.ranking and int(university.ranking.split('-')[0]) <= 100:
                reasons.append("Well-ranked institution")
        except:
            pass

        # Default reason if none found
        if not reasons:
            reasons.append("Excellent match for your profile")

        return "; ".join(reasons[:2])  # Limit to 2 reasons