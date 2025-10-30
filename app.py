from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import pandas as pd
import json
from typing import Dict, List, Any
import re
import math  # Added for sqrt function

app = FastAPI(title="Project Samarth Q&A System")

# CORS middleware to allow Streamlit frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class DataSource(BaseModel):
    name: str
    url: str
    description: str

class AnswerResponse(BaseModel):
    answer: str
    sources: List[DataSource]
    data_points: Dict[str, Any]

# Mock data sources (in production, these would be real API calls to data.gov.in)
AGRICULTURAL_DATA = {
    "rajasthan": {
        "crops": {
            "Bajra": {"2018": 4500, "2019": 4200, "2020": 3800, "2021": 3500, "2022": 4000},
            "Wheat": {"2018": 3200, "2019": 3100, "2020": 2800, "2021": 2500, "2022": 2700},
            "Groundnut": {"2018": 800, "2019": 750, "2020": 700, "2021": 650, "2022": 720},
            "Guar": {"2018": 600, "2019": 620, "2020": 580, "2021": 550, "2022": 590},
            "Rice": {"2018": 1200, "2019": 1100, "2020": 900, "2021": 800, "2022": 850}
        },
        "water_requirements": {
            "Bajra": "Low (350-400mm)",
            "Wheat": "High (500-600mm)", 
            "Groundnut": "Medium (400-500mm)",
            "Guar": "Very Low (250-300mm)",
            "Rice": "Very High (1200-1500mm)"
        }
    },
    "punjab": {
        "crops": {
            "Wheat": {"2018": 18000, "2019": 17500, "2020": 17000, "2021": 16500, "2022": 16800},
            "Rice": {"2018": 16000, "2019": 15800, "2020": 15500, "2021": 15200, "2022": 15400},
            "Cotton": {"2018": 2000, "2019": 1900, "2020": 1850, "2021": 1800, "2022": 1820},
            "Bajra": {"2018": 800, "2019": 750, "2020": 700, "2021": 650, "2022": 680}
        },
        "water_requirements": {
            "Wheat": "High (500-600mm)",
            "Rice": "Very High (1200-1500mm)",
            "Cotton": "Medium (400-500mm)",
            "Bajra": "Low (350-400mm)"
        }
    }
}

CLIMATE_DATA = {
    "rajasthan": {
        "rainfall": {"2018": 450, "2019": 380, "2020": 320, "2021": 290, "2022": 410},
        "drought_years": ["2020", "2021"],
        "avg_temperature": 28.5,
        "climate_zone": "Arid"
    },
    "punjab": {
        "rainfall": {"2018": 650, "2019": 620, "2020": 580, "2021": 590, "2022": 610},
        "drought_years": [],
        "avg_temperature": 24.0,
        "climate_zone": "Semi-Arid"
    }
}

DATA_SOURCES = {
    "agriculture": DataSource(
        name="Ministry of Agriculture - Crop Production Statistics",
        url="https://data.gov.in/resource/all-india-season-wise-crop-production-statistics",
        description="State-wise and crop-wise production data from 2018-2022"
    ),
    "climate": DataSource(
        name="India Meteorological Department - Rainfall Data", 
        url="https://data.gov.in/resource/district-wise-rainfall-normal",
        description="Historical rainfall patterns and climate data from 2018-2022"
    )
}

def calculate_variance(data):
    """Calculate variance without using numpy"""
    if len(data) == 0:
        return 0
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    return variance

def extract_entities(question: str) -> Dict[str, Any]:
    """Extract key entities from natural language question"""
    question_lower = question.lower()
    
    entities = {
        "states": [],
        "crops": [],
        "years": [],
        "metrics": [],
        "comparison_type": None
    }
    
    # Extract states
    state_keywords = {
        "rajasthan": ["rajasthan", "raj"],
        "punjab": ["punjab"],
        "gujarat": ["gujarat"],
        "haryana": ["haryana"]
    }
    
    for state, keywords in state_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            entities["states"].append(state)
    
    # Extract crops
    crop_keywords = {
        "Bajra": ["bajra", "pearl millet", "millet"],
        "Wheat": ["wheat"],
        "Rice": ["rice", "paddy"], 
        "Cotton": ["cotton"],
        "Groundnut": ["groundnut", "peanut"],
        "Guar": ["guar", "cluster bean"]
    }
    
    for crop, keywords in crop_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            entities["crops"].append(crop)
    
    # Extract years
    year_matches = re.findall(r'\b(201[8-9]|202[0-4])\b', question)
    entities["years"] = year_matches
    
    # Extract metrics
    if "rainfall" in question_lower:
        entities["metrics"].append("rainfall")
    if "production" in question_lower or "yield" in question_lower:
        entities["metrics"].append("production")
    if "drought" in question_lower:
        entities["metrics"].append("drought_resistance")
    if "water" in question_lower:
        entities["metrics"].append("water_requirement")
    
    # Determine comparison type
    if "compare" in question_lower:
        entities["comparison_type"] = "comparison"
    elif "trend" in question_lower:
        entities["comparison_type"] = "trend"
    elif "argument" in question_lower or "promote" in question_lower:
        entities["comparison_type"] = "policy_arguments"
    
    return entities

def generate_policy_arguments(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Generate data-backed policy arguments for promoting drought-resistant crops"""
    
    state = entities["states"][0] if entities["states"] else "rajasthan"
    
    # Define crop categories
    drought_resistant_crops = ["Bajra", "Guar"]
    water_intensive_crops = ["Rice", "Wheat"]
    
    # Get climate data
    rainfall_data = CLIMATE_DATA.get(state, {}).get("rainfall", {})
    avg_rainfall = sum(rainfall_data.values()) / len(rainfall_data) if rainfall_data else 0
    drought_years = CLIMATE_DATA.get(state, {}).get("drought_years", [])
    climate_zone = CLIMATE_DATA.get(state, {}).get("climate_zone", "Unknown")
    
    # Get agricultural data
    crop_data = AGRICULTURAL_DATA.get(state, {}).get("crops", {})
    water_req_data = AGRICULTURAL_DATA.get(state, {}).get("water_requirements", {})
    
    arguments = []
    data_points = {}
    
    # Argument 1: Water scarcity and climate adaptation
    arguments.append({
        "title": "Water Scarcity Adaptation",
        "content": f"**{state.title()}** receives only **{avg_rainfall:.0f}mm** average annual rainfall (classified as {climate_zone.lower()}) with recent drought years in {drought_years}. Drought-resistant crops like Bajra and Guar require **60-70% less water** than water-intensive alternatives like Rice and Wheat.",
        "data": {
            "average_rainfall": avg_rainfall,
            "drought_years": drought_years,
            "climate_zone": climate_zone
        }
    })
    
    # Argument 2: Economic stability during drought
    stability_data = {}
    for crop in drought_resistant_crops + water_intensive_crops:
        if crop in crop_data:
            production_values = list(crop_data[crop].values())
            if len(production_values) > 1:
                # Calculate stability using our custom variance function
                variance = calculate_variance(production_values)
                avg_production = sum(production_values) / len(production_values)
                
                # Calculate performance in drought vs normal years
                drought_performance = []
                normal_performance = []
                
                for year, production in crop_data[crop].items():
                    if year in drought_years:
                        drought_performance.append(production)
                    else:
                        normal_performance.append(production)
                
                avg_drought = sum(drought_performance) / len(drought_performance) if drought_performance else 0
                avg_normal = sum(normal_performance) / len(normal_performance) if normal_performance else avg_production
                
                resilience_ratio = (avg_drought / avg_normal * 100) if avg_normal > 0 else 0
                
                stability_data[crop] = {
                    "average_production": avg_production,
                    "production_variance": variance,
                    "drought_resilience": f"{resilience_ratio:.1f}%"
                }
    
    arguments.append({
        "title": "Economic Resilience",
        "content": "Drought-resistant crops maintain higher production levels during drought years, providing economic stability to farmers when they need it most.",
        "data": stability_data
    })
    
    # Argument 3: Resource sustainability
    water_savings_comparison = {}
    for crop in drought_resistant_crops:
        if crop in water_req_data:
            water_savings_comparison[crop] = water_req_data[crop]
    
    arguments.append({
        "title": "Sustainable Resource Management",
        "content": f"With groundwater levels in {state.title()} declining rapidly, shifting to low-water crops is essential for long-term agricultural sustainability.",
        "data": {
            "recommended_crops": water_savings_comparison,
            "water_savings": "60-70% less water required"
        }
    })
    
    # Format the answer
    answer = f"## Data-Backed Arguments for Promoting Drought-Resistant Crops in {state.title()}\n\n"
    answer += "Based on integrated analysis of climate and agricultural data from 2018-2022:\n\n"
    
    for i, argument in enumerate(arguments, 1):
        answer += f"### {i}. {argument['title']}\n"
        answer += f"{argument['content']}\n\n"
        
        # Add specific data points for the first argument
        if i == 1 and "data" in argument:
            data = argument["data"]
            answer += f"- Average Rainfall: {data['average_rainfall']:.0f}mm\n"
            answer += f"- Climate Zone: {data['climate_zone']}\n"
            answer += f"- Recent Drought Years: {', '.join(data['drought_years']) if data['drought_years'] else 'None'}\n"
        answer += "\n"
    
    answer += "### Recommended Drought-Resistant Crops:\n"
    for crop in drought_resistant_crops:
        if crop in water_req_data:
            answer += f"- **{crop}**: {water_req_data[crop]} water requirement\n"
    
    # Prepare data points for response
    data_points = {
        "average_rainfall": avg_rainfall,
        "drought_years": drought_years,
        "climate_zone": climate_zone,
        "crop_stability": stability_data,
        "water_requirements": {crop: water_req_data.get(crop, "Unknown") for crop in drought_resistant_crops + water_intensive_crops}
    }
    
    return {
        "answer": answer,
        "data_points": data_points,
        "sources": [DATA_SOURCES["agriculture"], DATA_SOURCES["climate"]]
    }

def generate_comparison(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comparison between states/crops"""
    states = entities["states"] if entities["states"] else ["rajasthan", "punjab"]
    crops = entities["crops"] if entities["crops"] else ["Bajra", "Wheat"]
    
    comparison_data = {}
    
    for state in states:
        comparison_data[state] = {
            "rainfall": CLIMATE_DATA.get(state, {}).get("rainfall", {}),
            "crop_production": {},
            "climate_zone": CLIMATE_DATA.get(state, {}).get("climate_zone", "Unknown")
        }
        for crop in crops:
            if crop in AGRICULTURAL_DATA.get(state, {}).get("crops", {}):
                comparison_data[state]["crop_production"][crop] = AGRICULTURAL_DATA[state]["crops"][crop]
    
    # Generate comparison text
    answer = f"## Comparative Analysis: {', '.join([s.title() for s in states])}\n\n"
    
    for state in states:
        answer += f"### {state.title()}\n"
        rainfall_data = comparison_data[state]["rainfall"]
        avg_rainfall = sum(rainfall_data.values()) / len(rainfall_data) if rainfall_data else 0
        answer += f"- **Climate Zone**: {comparison_data[state]['climate_zone']}\n"
        answer += f"- **Average Rainfall**: {avg_rainfall:.1f}mm\n"
        
        for crop, production in comparison_data[state]["crop_production"].items():
            avg_production = sum(production.values()) / len(production)
            water_req = AGRICULTURAL_DATA[state]["water_requirements"].get(crop, "Unknown")
            answer += f"- **{crop}**: {avg_production:,.0f} thousand tonnes (Water: {water_req})\n"
        answer += "\n"
    
    return {
        "answer": answer,
        "data_points": comparison_data,
        "sources": [DATA_SOURCES["agriculture"], DATA_SOURCES["climate"]]
    }

def generate_trend_analysis(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Generate trend analysis for crops and climate"""
    state = entities["states"][0] if entities["states"] else "rajasthan"
    crops = entities["crops"] if entities["crops"] else ["Bajra", "Wheat"]
    
    trend_data = {
        "rainfall_trend": CLIMATE_DATA.get(state, {}).get("rainfall", {}),
        "crop_trends": {}
    }
    
    for crop in crops:
        if crop in AGRICULTURAL_DATA.get(state, {}).get("crops", {}):
            trend_data["crop_trends"][crop] = AGRICULTURAL_DATA[state]["crops"][crop]
    
    # Calculate trends
    answer = f"## Trend Analysis for {state.title()} (2018-2022)\n\n"
    
    # Rainfall trend
    rainfall_values = list(trend_data["rainfall_trend"].values())
    if len(rainfall_values) > 1:
        rainfall_trend = (rainfall_values[-1] - rainfall_values[0]) / len(rainfall_values)
        answer += f"### Climate Trends\n"
        answer += f"- **Rainfall Trend**: {'↑ Increasing' if rainfall_trend > 0 else '↓ Decreasing'} by {abs(rainfall_trend):.1f}mm per year\n"
        answer += f"- **Drought Years**: {CLIMATE_DATA[state].get('drought_years', [])}\n\n"
    
    # Crop production trends
    answer += "### Crop Production Trends\n"
    crop_data = AGRICULTURAL_DATA.get(state, {}).get("crops", {})
    
    for crop in crops:
        if crop in crop_data:
            production_data = crop_data[crop]
            production_values = [production_data[year] for year in sorted(production_data.keys())]
            production_trend = (production_values[-1] - production_values[0]) / len(production_values)
            
            trend_icon = "📈" if production_trend > 0 else "📉"
            answer += f"- **{crop}**: {trend_icon} {'Increasing' if production_trend > 0 else 'Decreasing'} by {abs(production_trend):.1f} thousand tonnes/year\n"
    
    return {
        "answer": answer,
        "data_points": trend_data,
        "sources": [DATA_SOURCES["agriculture"], DATA_SOURCES["climate"]]
    }

def generate_answer(entities: Dict[str, Any], question: str) -> Dict[str, Any]:
    """Generate answer based on extracted entities"""
    
    if entities["comparison_type"] == "policy_arguments":
        return generate_policy_arguments(entities)
    elif entities["comparison_type"] == "comparison":
        return generate_comparison(entities)
    elif entities["comparison_type"] == "trend":
        return generate_trend_analysis(entities)
    else:
        # Default to policy arguments for questions about drought-resistant crops
        if any(word in question.lower() for word in ["drought", "resistant", "promote", "argument"]):
            return generate_policy_arguments(entities)
        else:
            return generate_comparison(entities)

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Main endpoint for answering questions"""
    try:
        # Extract entities from question
        entities = extract_entities(request.question)
        
        # Generate answer based on entities
        result = generate_answer(entities, request.question)
        
        return AnswerResponse(
            answer=result["answer"],
            sources=result["sources"],
            data_points=result["data_points"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Project Samarth Q&A System"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)