"""Seed script to create sample brief templates."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine
from app.core.config import settings
from app.models.brief_template import BriefTemplate


def seed_brief_templates():
    """Create sample brief templates."""
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Check if templates already exist
        existing_templates = session.query(BriefTemplate).count()
        if existing_templates > 0:
            print("Brief templates already exist. Skipping seed.")
            return
        
        # Fashion/Beauty Template
        fashion_template = BriefTemplate(
            name="Fashion Product Launch",
            description="Template for fashion and beauty product launches",
            content="""
# {{campaign_name}} - Product Launch Brief

## Campaign Overview
We're excited to partner with you for the launch of {{product_name}}!

## Deliverables
{{#deliverables}}
- {{.}}
{{/deliverables}}

## Key Messages
- Highlight the unique features of {{product_name}}
- Emphasize {{brand_values}}
- Use hashtags: {{hashtags}}

## Timeline
- Content creation deadline: {{creation_deadline}}
- Publishing date: {{publish_date}}

## Compensation
- Fee: {{compensation_amount}} {{currency}}
- Additional perks: {{perks}}

## Brand Guidelines
- Maintain authentic voice while highlighting product benefits
- Include clear product shots
- Tag @{{brand_handle}} in all posts

## Contact
For questions, contact: {{contact_email}}
            """.strip(),
            variables={
                "campaign_name": "",
                "product_name": "",
                "deliverables": ["1 Instagram post", "3 Instagram stories"],
                "brand_values": "",
                "hashtags": "",
                "creation_deadline": "",
                "publish_date": "",
                "compensation_amount": "",
                "currency": "THB",
                "perks": "",
                "brand_handle": "",
                "contact_email": ""
            },
            category="fashion",
            is_active=True,
            is_default=True,
            created_by=1  # Admin user
        )
        session.add(fashion_template)
        
        # Tech Product Template
        tech_template = BriefTemplate(
            name="Tech Product Review",
            description="Template for technology product reviews and unboxings",
            content="""
# {{campaign_name}} - Tech Review Brief

## Product Information
Product: {{product_name}}
Brand: {{brand_name}}
Key Features: {{key_features}}

## Content Requirements
{{#deliverables}}
- {{.}}
{{/deliverables}}

## Review Guidelines
- Provide honest, authentic review
- Highlight key features: {{key_features}}
- Include unboxing footage if applicable
- Show product in use
- Mention pros and cons fairly

## Technical Specifications to Mention
{{#tech_specs}}
- {{.}}
{{/tech_specs}}

## Timeline
- Product delivery: {{delivery_date}}
- Content deadline: {{content_deadline}}
- Go-live date: {{publish_date}}

## Compensation
- Fee: {{fee_amount}} {{currency}}
- Product value: {{product_value}} {{currency}}
- Keep the product: {{keep_product}}

## Hashtags
{{hashtags}}

## Contact
Questions? Reach out to {{contact_person}} at {{contact_email}}
            """.strip(),
            variables={
                "campaign_name": "",
                "product_name": "",
                "brand_name": "",
                "key_features": "",
                "deliverables": ["1 YouTube review video", "1 Instagram post", "3 Instagram stories"],
                "tech_specs": [],
                "delivery_date": "",
                "content_deadline": "",
                "publish_date": "",
                "fee_amount": "",
                "currency": "THB",
                "product_value": "",
                "keep_product": "Yes",
                "hashtags": "",
                "contact_person": "",
                "contact_email": ""
            },
            category="technology",
            is_active=True,
            created_by=1
        )
        session.add(tech_template)
        
        # Food & Lifestyle Template
        food_template = BriefTemplate(
            name="Restaurant/Food Brand",
            description="Template for restaurant and food brand collaborations",
            content="""
# {{campaign_name}} - Food Collaboration Brief

## Restaurant/Brand Information
Name: {{restaurant_name}}
Location: {{location}}
Cuisine Type: {{cuisine_type}}
Special Offers: {{special_offers}}

## Content Deliverables
{{#deliverables}}
- {{.}}
{{/deliverables}}

## Content Guidelines
- Showcase the ambiance and food presentation
- Highlight signature dishes: {{signature_dishes}}
- Include location tag: {{location_tag}}
- Mention any special promotions: {{promotions}}
- Show the dining experience authentically

## Must-Include Elements
- Clear food photography/videography
- Restaurant exterior/interior shots
- Price range mention (if applicable)
- Personal dining experience
- Recommendation to followers

## Timeline
- Visit date: {{visit_date}}
- Content posting: {{posting_date}}
- Story highlights: {{story_duration}}

## Compensation
- Complimentary meal for {{guest_count}} people
- Additional fee: {{additional_fee}} {{currency}}
- Value: {{meal_value}} {{currency}}

## Hashtags & Tags
- Tag: @{{restaurant_handle}}
- Hashtags: {{hashtags}}
- Location: {{location_tag}}

## Contact
Reservation and questions: {{contact_person}} - {{contact_phone}}
            """.strip(),
            variables={
                "campaign_name": "",
                "restaurant_name": "",
                "location": "",
                "cuisine_type": "",
                "special_offers": "",
                "deliverables": ["1 Instagram post", "5 Instagram stories", "1 Reel"],
                "signature_dishes": "",
                "location_tag": "",
                "promotions": "",
                "visit_date": "",
                "posting_date": "",
                "story_duration": "24 hours",
                "guest_count": "2",
                "additional_fee": "0",
                "currency": "THB",
                "meal_value": "",
                "restaurant_handle": "",
                "hashtags": "",
                "contact_person": "",
                "contact_phone": ""
            },
            category="food",
            is_active=True,
            created_by=1
        )
        session.add(food_template)
        
        session.commit()
        print("✅ Brief templates seeded successfully!")
        print("\nCreated templates:")
        print("  1. Fashion Product Launch")
        print("  2. Tech Product Review") 
        print("  3. Restaurant/Food Brand")


if __name__ == "__main__":
    seed_brief_templates()