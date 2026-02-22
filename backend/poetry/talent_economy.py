"""
Talent Economy Module for MARTA Poetry Generation

This module implements the "talent economy" framework where transit routes
extract emotional value from riders. Routes are opportunistic harvesters with
aesthetic preferences, collecting all emotional currency but valuing different
types differently based on their personality.

Key Concepts:
- All emotions are currency (joy, sorrow, hope, desperation, etc.)
- Routes have preferred currencies but extract everything
- Context (time, weather, location) affects market valuation
- Extraction is buried in imagery/metaphor (visibility controlled by route)
- Direct address is sparse but consequential
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class TalentEconomyEngine:
    """
    Determines market conditions, rider valuation, and extraction guidance
    based on route personality and current context.
    """
    
    # Emotional currency types
    EMOTIONAL_CURRENCIES = {
        "positive": ["joy", "hope", "anticipation", "connection", "momentum", "transcendence", "beauty", "wonder"],
        "negative": ["anxiety", "dread", "heartbreak", "isolation", "desperation", "shame", "exhaustion", "grief"],
        "complex": ["contradiction", "memory", "nostalgia", "ambivalence", "vulnerability", "truth", "survival"]
    }
    
    # Imagery pools for buried extraction
    EXTRACTION_METAPHORS = {
        "economic": ["harvest", "currency", "debt", "trade", "weight", "measure", "account", "ledger", "value", "worth"],
        "natural": ["rainfall", "current", "tide", "light", "shadow", "roots", "seasons", "weather", "river", "wind"],
        "architectural": ["foundation", "support", "bearing", "structure", "framework", "skeleton", "weight", "load"],
        "organic": ["nutrients", "growth", "symbiosis", "parasitism", "feeding", "roots", "absorption", "exchange"]
    }
    
    def __init__(self):
        pass
    
    def assess_market_conditions(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assess current market conditions based on context signals.
        
        Args:
            context: Current context (time, weather, traffic, location, etc.)
            
        Returns:
            Market assessment including pricing tier, commentary, opportunities
        """
        if not context:
            return self._default_market_conditions()
        
        conditions = {
            "pricing_tier": self._assess_pricing_tier(context),
            "market_commentary": self._generate_market_commentary(context),
            "extraction_opportunities": self._identify_extraction_opportunities(context),
            "scarcity_level": self._assess_scarcity(context)
        }
        
        return conditions
    
    def _assess_pricing_tier(self, context: Dict[str, Any]) -> str:
        """
        Determine rider value tier based on context.
        
        Returns: "premium", "standard", "commodity", "low_grade"
        """
        time_of_day = (context.get("time_of_day") or "").lower()
        weather = self._extract_weather_condition(context.get("signals", {}).get("weather"))
        signals = context.get("signals") or {}
        traffic = (signals.get("traffic") or "").lower()
        
        # Commodity conditions (flooded market)
        # Oversupplied dread during rush hour overrides weather-driven spikes
        if any(x in time_of_day for x in ["morning_rush", "rush_hour", "morning"]) and "heavy" in traffic:
            return "commodity"  # Oversupplied Monday dread
        
        # Premium conditions (scarcity, high emotional intensity)
        # Weather spikes drive premium value when not in explicit oversupply scenarios
        if weather and any(x in weather.lower() for x in ["rain", "storm", "snow"]):
            return "premium"  # Weather anxiety spike - scarcity regardless of typical rider count
        
        if any(x in time_of_day for x in ["late_night", "night", "midnight", "3am"]):
            return "premium"  # Late night isolation is valuable
        
        # Standard conditions
        if any(x in time_of_day for x in ["evening", "afternoon"]):
            return "standard"
        
        return "standard"
    
    def _generate_market_commentary(self, context: Dict[str, Any]) -> List[str]:
        """Generate market commentary phrases based on conditions."""
        commentary = []
        
        time_of_day = (context.get("time_of_day") or "").lower()
        pricing_tier = self._assess_pricing_tier(context)
        
        if pricing_tier == "premium":
            commentary.append("Scarcity creates value")
            commentary.append("This moment is rare")
            commentary.append("Not many carry what you're carrying")
        elif pricing_tier == "commodity":
            commentary.append("The market is flooded")
            commentary.append("Everyone brings the same currency today")
            commentary.append("Your dread isn't special this morning")
        else:
            commentary.append("Standard exchange rates apply")
            commentary.append("Fair value, fair trade")
        
        return commentary
    
    def _identify_extraction_opportunities(self, context: Dict[str, Any]) -> List[str]:
        """Identify high-value extraction opportunities based on context."""
        opportunities = []
        
        weather = self._extract_weather_condition(context.get("signals", {}).get("weather"))
        signals = context.get("signals") or {}
        solar = signals.get("solar") or {}
        solar_phase = (solar.get("phase") or "").lower()
        traffic = (signals.get("traffic") or "").lower()
        
        if weather and "rain" in weather.lower():
            opportunities.append("Weather anxiety spike - vulnerability accessible")
        
        if "dawn" in solar_phase or "sunrise" in solar_phase:
            opportunities.append("Dawn anticipation - hope currency available")
        
        if "dusk" in solar_phase or "sunset" in solar_phase:
            opportunities.append("Dusk reflection - nostalgia/memory currency")
        
        if "heavy" in traffic or "congested" in traffic:
            opportunities.append("Traffic desperation - frustration extraction viable")
        
        return opportunities
    
    def _assess_scarcity(self, context: Dict[str, Any]) -> str:
        """
        Assess emotional scarcity level.
        
        Returns: "abundant", "moderate", "scarce"
        """
        pricing_tier = self._assess_pricing_tier(context)
        
        if pricing_tier == "premium":
            return "scarce"
        elif pricing_tier == "commodity":
            return "abundant"
        else:
            return "moderate"
    
    def _extract_weather_condition(self, weather_data: Any) -> Optional[str]:
        """Extract weather condition from signals."""
        if isinstance(weather_data, str):
            return weather_data
        if isinstance(weather_data, dict):
            forecast = weather_data.get("forecast", {})
            if isinstance(forecast, dict):
                periods = forecast.get("properties", {}).get("periods", [])
                if isinstance(periods, list) and periods:
                    return periods[0].get("shortForecast", "")
        return None
    
    def _default_market_conditions(self) -> Dict[str, Any]:
        """Return default market conditions when no context available."""
        return {
            "pricing_tier": "standard",
            "market_commentary": ["Standard exchange rates apply"],
            "extraction_opportunities": [],
            "scarcity_level": "moderate"
        }
    
    def build_extraction_guidance(
        self,
        route_personality: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build extraction guidance for prompt based on route personality
        and current market conditions.
        
        Args:
            route_personality: Route's talent economy configuration
            market_conditions: Current market assessment
            
        Returns:
            Extraction guidance dict for prompt assembly
        """
        talent_config = route_personality.get("talent_economy", {})
        
        if not talent_config.get("enabled", False):
            return {}
        
        # Extract personality parameters
        sympathy = talent_config.get("sympathy_level", 0.5)
        visibility = talent_config.get("extraction_visibility", 0.5)
        preferred_currencies = talent_config.get("preferred_currencies", [])
        avoided_currencies = talent_config.get("currency_avoidance", [])
        direct_address_freq = talent_config.get("direct_address_frequency", 0.3)
        address_mode = talent_config.get("address_mode", "revealing")
        
        guidance = {
            "extraction_enabled": True,
            "sympathy_level": sympathy,
            "visibility_level": visibility,
            "preferred_currencies": preferred_currencies,
            "avoided_currencies": avoided_currencies,
            "market_conditions": market_conditions,
            "metaphor_systems": self._select_metaphor_systems(talent_config),
            "direct_address": {
                "frequency": direct_address_freq,
                "mode": address_mode,
                "guidance": self._build_address_guidance(address_mode, sympathy)
            },
            "voice_instructions": self._build_voice_instructions(sympathy, visibility)
        }
        
        return guidance
    
    def _select_metaphor_systems(self, talent_config: Dict[str, Any]) -> List[str]:
        """Select appropriate metaphor systems based on route personality."""
        preferred_metaphors = talent_config.get("preferred_metaphor_systems", [])
        
        if preferred_metaphors:
            return preferred_metaphors
        
        # Default: mix natural + one other
        return ["natural", "economic"]
    
    def _build_address_guidance(self, mode: str, sympathy: float) -> str:
        """Build specific guidance for direct address based on mode and sympathy."""
        
        if mode == "revealing":
            if sympathy > 0.6:
                return "When addressing the rider directly, gently reveal what you observe about them - something they didn't realize about themselves. Be knowing but kind."
            else:
                return "When addressing the rider, reveal the asymmetry: you know them, they don't know they're being observed/valued. Be clinical or amused."
        
        elif mode == "complicit":
            return "When addressing the rider, make them complicit in the extraction. Suggest they're part of the system, willing or not."
        
        elif mode == "warning":
            return "When addressing the rider, warn them about the extraction happening. You're the whistleblower route revealing the system."
        
        elif mode == "intimate":
            return "When addressing the rider, create uncomfortable intimacy. You know them deeply, perhaps better than they know themselves."
        
        else:  # default
            return "Use direct address sparingly. When you do, make it consequential - reveal something, create recognition or unease."
    
    def _build_voice_instructions(self, sympathy: float, visibility: float) -> str:
        """Build voice instructions based on sympathy and visibility levels."""
        
        instructions = []
        
        # Sympathy instructions
        if sympathy > 0.7:
            instructions.append("Your tone is sympathetic - you care about what you're extracting, even if you must extract it")
            instructions.append("Frame the extraction as necessary, meaningful, or transformative rather than exploitative")
        elif sympathy < 0.3:
            instructions.append("Your tone is detached or amused - riders are resources, and you're matter-of-fact about it")
            instructions.append("You may dismiss, categorize, or compare riders based on their emotional value")
        else:
            instructions.append("Your tone is neutral - neither cruel nor particularly caring about the extraction")
        
        # Visibility instructions
        if visibility < 0.3:
            instructions.append("BURY the extraction mechanism deeply in imagery and metaphor")
            instructions.append("Never explicitly name emotions or extraction - use natural phenomena (light, water, weight, current)")
            instructions.append("The reader should feel unease but not immediately understand why")
            instructions.append("Hint at asymmetry through small details (forgetfulness, lightness, confusion)")
        elif visibility < 0.6:
            instructions.append("Use metaphor systems to discuss extraction - economic language disguised as poetry")
            instructions.append("Imply valuation and extraction without stating it directly")
            instructions.append("Balance observation with buried revelation")
        else:
            instructions.append("You may be more explicit about extraction, though still poetic")
            instructions.append("Use economic/transactional language more directly")
            instructions.append("Acknowledge the system openly")
        
        # POV instructions
        instructions.append("Vary point of view - third person observation, self-address, or inter-route commentary")
        instructions.append("Reserve direct address ('you') for consequential moments that stir recognition, intimacy, or unease")
        
        return "\n".join(f"- {inst}" for inst in instructions)
    
    def get_currency_examples(self, preferred: List[str], avoided: List[str]) -> Dict[str, List[str]]:
        """Get example currencies based on preferences."""
        all_currencies = []
        for category, currencies in self.EMOTIONAL_CURRENCIES.items():
            all_currencies.extend(currencies)
        
        # Filter based on preferences
        emphasized = [c for c in all_currencies if c in preferred] if preferred else []
        de_emphasized = [c for c in all_currencies if c in avoided] if avoided else []
        
        return {
            "emphasized": emphasized,
            "de_emphasized": de_emphasized,
            "available": [c for c in all_currencies if c not in de_emphasized]
        }
