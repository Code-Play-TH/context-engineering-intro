"""
Variable mapping system for report templates.

This module defines all available template variables and their data sources.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from decimal import Decimal


class VariableMapper:
    """Handles mapping of template variables to campaign data."""
    
    def __init__(self):
        self.formatters = VariableFormatters()
    
    def get_available_variables(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available template variables with their descriptions and categories.
        
        Returns:
            Dictionary with variable info including description, category, and example
        """
        return {
            # Campaign Information
            '{{campaign_name}}': {
                'category': 'Campaign Info',
                'description': 'Campaign name',
                'example': 'Summer Fashion Campaign 2024',
                'data_type': 'string'
            },
            '{{campaign_start_date}}': {
                'category': 'Campaign Info',
                'description': 'Campaign start date',
                'example': 'January 15, 2024',
                'data_type': 'date'
            },
            '{{campaign_end_date}}': {
                'category': 'Campaign Info',
                'description': 'Campaign end date',
                'example': 'March 15, 2024',
                'data_type': 'date'
            },
            '{{campaign_budget}}': {
                'category': 'Campaign Info',
                'description': 'Total campaign budget',
                'example': '50,000.00',
                'data_type': 'currency'
            },
            '{{campaign_currency}}': {
                'category': 'Campaign Info',
                'description': 'Campaign currency code',
                'example': 'USD',
                'data_type': 'string'
            },
            '{{campaign_status}}': {
                'category': 'Campaign Info',
                'description': 'Current campaign status',
                'example': 'Active',
                'data_type': 'string'
            },
            '{{campaign_objectives}}': {
                'category': 'Campaign Info',
                'description': 'Campaign objectives and goals',
                'example': 'Increase brand awareness and drive sales',
                'data_type': 'text'
            },
            '{{campaign_duration_days}}': {
                'category': 'Campaign Info',
                'description': 'Campaign duration in days',
                'example': '60',
                'data_type': 'number'
            },
            
            # KOL Metrics
            '{{kol_count}}': {
                'category': 'KOL Metrics',
                'description': 'Total number of KOLs in campaign',
                'example': '15',
                'data_type': 'number'
            },
            '{{total_reach}}': {
                'category': 'KOL Metrics',
                'description': 'Combined follower count of all KOLs',
                'example': '2,500,000',
                'data_type': 'number'
            },
            '{{total_engagement}}': {
                'category': 'KOL Metrics',
                'description': 'Total engagement across all posts',
                'example': '125,000',
                'data_type': 'number'
            },
            '{{avg_engagement_rate}}': {
                'category': 'KOL Metrics',
                'description': 'Average engagement rate across all KOLs',
                'example': '3.2%',
                'data_type': 'percentage'
            },
            '{{top_performing_kol}}': {
                'category': 'KOL Metrics',
                'description': 'Name of top performing KOL',
                'example': 'Jane Smith (@janesmith)',
                'data_type': 'string'
            },
            '{{avg_follower_count}}': {
                'category': 'KOL Metrics',
                'description': 'Average follower count per KOL',
                'example': '166,667',
                'data_type': 'number'
            },
            
            # Content Metrics
            '{{total_posts}}': {
                'category': 'Content Metrics',
                'description': 'Total number of campaign posts',
                'example': '45',
                'data_type': 'number'
            },
            '{{total_likes}}': {
                'category': 'Content Metrics',
                'description': 'Total likes across all posts',
                'example': '85,000',
                'data_type': 'number'
            },
            '{{total_comments}}': {
                'category': 'Content Metrics',
                'description': 'Total comments across all posts',
                'example': '12,500',
                'data_type': 'number'
            },
            '{{total_shares}}': {
                'category': 'Content Metrics',
                'description': 'Total shares across all posts',
                'example': '8,200',
                'data_type': 'number'
            },
            '{{total_views}}': {
                'category': 'Content Metrics',
                'description': 'Total views across all posts',
                'example': '1,200,000',
                'data_type': 'number'
            },
            '{{avg_likes_per_post}}': {
                'category': 'Content Metrics',
                'description': 'Average likes per post',
                'example': '1,889',
                'data_type': 'number'
            },
            '{{avg_comments_per_post}}': {
                'category': 'Content Metrics',
                'description': 'Average comments per post',
                'example': '278',
                'data_type': 'number'
            },
            
            # Performance Metrics
            '{{cpm}}': {
                'category': 'Performance Metrics',
                'description': 'Cost per mille (thousand impressions)',
                'example': '$2.50',
                'data_type': 'currency'
            },
            '{{cpe}}': {
                'category': 'Performance Metrics',
                'description': 'Cost per engagement',
                'example': '$0.40',
                'data_type': 'currency'
            },
            '{{roi_percentage}}': {
                'category': 'Performance Metrics',
                'description': 'Return on investment percentage',
                'example': '250%',
                'data_type': 'percentage'
            },
            '{{conversion_rate}}': {
                'category': 'Performance Metrics',
                'description': 'Conversion rate from campaign',
                'example': '2.8%',
                'data_type': 'percentage'
            },
            
            # Platform Breakdown
            '{{instagram_posts}}': {
                'category': 'Platform Metrics',
                'description': 'Number of Instagram posts',
                'example': '25',
                'data_type': 'number'
            },
            '{{tiktok_posts}}': {
                'category': 'Platform Metrics',
                'description': 'Number of TikTok posts',
                'example': '12',
                'data_type': 'number'
            },
            '{{youtube_posts}}': {
                'category': 'Platform Metrics',
                'description': 'Number of YouTube posts',
                'example': '5',
                'data_type': 'number'
            },
            '{{facebook_posts}}': {
                'category': 'Platform Metrics',
                'description': 'Number of Facebook posts',
                'example': '3',
                'data_type': 'number'
            },
            
            # Time-based Metrics
            '{{best_posting_time}}': {
                'category': 'Time Metrics',
                'description': 'Best performing posting time',
                'example': '2:00 PM - 4:00 PM',
                'data_type': 'string'
            },
            '{{best_posting_day}}': {
                'category': 'Time Metrics',
                'description': 'Best performing day of week',
                'example': 'Wednesday',
                'data_type': 'string'
            },
            
            # KPI Achievement
            '{{kpi_reach_target}}': {
                'category': 'KPI Metrics',
                'description': 'Target reach from KPIs',
                'example': '2,000,000',
                'data_type': 'number'
            },
            '{{kpi_reach_actual}}': {
                'category': 'KPI Metrics',
                'description': 'Actual reach achieved',
                'example': '2,500,000',
                'data_type': 'number'
            },
            '{{kpi_reach_achievement}}': {
                'category': 'KPI Metrics',
                'description': 'Reach achievement percentage',
                'example': '125%',
                'data_type': 'percentage'
            },
            '{{kpi_engagement_target}}': {
                'category': 'KPI Metrics',
                'description': 'Target engagement from KPIs',
                'example': '100,000',
                'data_type': 'number'
            },
            '{{kpi_engagement_actual}}': {
                'category': 'KPI Metrics',
                'description': 'Actual engagement achieved',
                'example': '125,000',
                'data_type': 'number'
            },
            '{{kpi_engagement_achievement}}': {
                'category': 'KPI Metrics',
                'description': 'Engagement achievement percentage',
                'example': '125%',
                'data_type': 'percentage'
            },
            '{{overall_kpi_achievement}}': {
                'category': 'KPI Metrics',
                'description': 'Overall KPI achievement percentage',
                'example': '118%',
                'data_type': 'percentage'
            },
            
            # Report Metadata
            '{{generation_date}}': {
                'category': 'Report Info',
                'description': 'Report generation date',
                'example': 'March 20, 2024',
                'data_type': 'date'
            },
            '{{generation_time}}': {
                'category': 'Report Info',
                'description': 'Report generation time',
                'example': '2:30 PM',
                'data_type': 'time'
            },
            '{{report_period}}': {
                'category': 'Report Info',
                'description': 'Reporting period',
                'example': 'January 15 - March 15, 2024',
                'data_type': 'string'
            },
            
            # Client Information
            '{{client_name}}': {
                'category': 'Client Info',
                'description': 'Client company name',
                'example': 'Fashion Brand Inc.',
                'data_type': 'string'
            },
            '{{client_logo}}': {
                'category': 'Client Info',
                'description': 'Client logo image path',
                'example': 'client_logo.png',
                'data_type': 'image'
            },
            '{{brand_name}}': {
                'category': 'Client Info',
                'description': 'Brand name being promoted',
                'example': 'StyleCo',
                'data_type': 'string'
            },
        }
    
    def get_variables_by_category(self) -> Dict[str, List[str]]:
        """Get variables grouped by category."""
        variables = self.get_available_variables()
        categories = {}
        
        for variable, info in variables.items():
            category = info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(variable)
        
        return categories
    
    def validate_variables(self, variables: List[str]) -> Dict[str, bool]:
        """
        Validate if variables are supported.
        
        Args:
            variables: List of variables to validate
            
        Returns:
            Dictionary with variable as key and validity as boolean value
        """
        available_variables = self.get_available_variables()
        return {
            var: var in available_variables 
            for var in variables
        }
    
    def get_variable_info(self, variable: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific variable."""
        available_variables = self.get_available_variables()
        return available_variables.get(variable)
    
    def suggest_variables(self, search_term: str) -> List[str]:
        """
        Suggest variables based on search term.
        
        Args:
            search_term: Term to search for in variable names and descriptions
            
        Returns:
            List of matching variable names
        """
        available_variables = self.get_available_variables()
        suggestions = []
        
        search_term = search_term.lower()
        
        for variable, info in available_variables.items():
            # Search in variable name
            if search_term in variable.lower():
                suggestions.append(variable)
                continue
            
            # Search in description
            if search_term in info['description'].lower():
                suggestions.append(variable)
                continue
            
            # Search in category
            if search_term in info['category'].lower():
                suggestions.append(variable)
        
        return suggestions


class VariableFormatters:
    """Formatters for different data types in template variables."""
    
    @staticmethod
    def format_number(value: Any) -> str:
        """Format numbers with commas for readability."""
        if value is None:
            return "N/A"
        
        if isinstance(value, (int, float, Decimal)):
            if isinstance(value, float):
                # Round floats to 2 decimal places if they have decimals
                if value % 1 == 0:
                    return f"{int(value):,}"
                else:
                    return f"{value:,.2f}"
            else:
                return f"{value:,}"
        
        return str(value)
    
    @staticmethod
    def format_currency(value: Any, currency: str = "USD") -> str:
        """Format currency values."""
        if value is None:
            return "N/A"
        
        if isinstance(value, (int, float, Decimal)):
            if currency == "USD":
                return f"${value:,.2f}"
            else:
                return f"{value:,.2f} {currency}"
        
        return str(value)
    
    @staticmethod
    def format_percentage(value: Any, decimal_places: int = 1) -> str:
        """Format percentage values."""
        if value is None:
            return "N/A"
        
        if isinstance(value, (int, float, Decimal)):
            return f"{value:.{decimal_places}f}%"
        
        return str(value)
    
    @staticmethod
    def format_date(value: Any, format_string: str = "%B %d, %Y") -> str:
        """Format date values."""
        if value is None:
            return "N/A"
        
        if isinstance(value, datetime):
            return value.strftime(format_string)
        elif hasattr(value, 'strftime'):
            return value.strftime(format_string)
        
        return str(value)
    
    @staticmethod
    def format_time(value: Any, format_string: str = "%I:%M %p") -> str:
        """Format time values."""
        if value is None:
            return "N/A"
        
        if isinstance(value, datetime):
            return value.strftime(format_string)
        elif hasattr(value, 'strftime'):
            return value.strftime(format_string)
        
        return str(value)
    
    @staticmethod
    def format_duration(start_date: Any, end_date: Any) -> str:
        """Calculate and format duration between two dates."""
        if not start_date or not end_date:
            return "N/A"
        
        try:
            if hasattr(start_date, 'date'):
                start_date = start_date.date()
            if hasattr(end_date, 'date'):
                end_date = end_date.date()
            
            duration = end_date - start_date
            days = duration.days
            
            if days == 1:
                return "1 day"
            else:
                return f"{days} days"
        except:
            return "N/A"


# Global instance for easy access
variable_mapper = VariableMapper()