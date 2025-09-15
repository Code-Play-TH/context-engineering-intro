"""
ERPNext integration service for ERP synchronization.

Handles API communication with ERPNext for data synchronization,
customer management, item management, and sales order processing.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.sales import Customer, CustomerRequirement
from app.models.product import Product
from app.models.production import ProductionOrder
from app.models.user import User

settings = get_settings()


class ERPNextError(Exception):
    """Custom exception for ERPNext API errors."""
    pass


class ERPNextAuthError(ERPNextError):
    """Exception for ERPNext authentication errors."""
    pass


class ERPNextService:
    """
    Service for integrating with ERPNext ERP system.
    
    Provides methods for syncing customers, items, sales orders,
    and work orders between the factory ERP and ERPNext.
    """
    
    def __init__(self):
        """Initialize ERPNext service with configuration."""
        self.base_url = settings.erpnext_base_url
        self.api_key = settings.erpnext_api_key
        self.api_secret = settings.erpnext_api_secret
        self.timeout = 30.0
        self.is_enabled = bool(self.base_url and self.api_key and self.api_secret)
        
        # API endpoints
        self.endpoints = {
            "customers": "/api/resource/Customer",
            "items": "/api/resource/Item",
            "sales_orders": "/api/resource/Sales Order",
            "work_orders": "/api/resource/Work Order",
            "quotations": "/api/resource/Quotation",
            "delivery_notes": "/api/resource/Delivery Note",
            "purchase_orders": "/api/resource/Purchase Order",
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get API headers for ERPNext requests.
        
        Returns:
            Dict containing authorization headers
        """
        return {
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get_url(self, endpoint: str) -> str:
        """
        Construct full URL for ERPNext API endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL string
        """
        if not self.base_url:
            raise ERPNextError("ERPNext base URL not configured")
        return urljoin(self.base_url, endpoint)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to ERPNext API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data for POST/PUT
            params: Query parameters
            
        Returns:
            Response data dictionary
            
        Raises:
            ERPNextError: If request fails or returns error
        """
        if not self.is_enabled:
            raise ERPNextError("ERPNext integration is not enabled or properly configured")
        
        url = self._get_url(endpoint)
        headers = self._get_headers()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ERPNextError(f"Unsupported HTTP method: {method}")
                
                # Check for authentication errors
                if response.status_code == 401:
                    raise ERPNextAuthError("ERPNext authentication failed. Check API credentials.")
                
                # Check for other HTTP errors
                if response.status_code >= 400:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_detail = error_data["message"]
                        elif "exc" in error_data:
                            error_detail = error_data["exc"]
                    except:
                        error_detail = response.text
                    
                    raise ERPNextError(f"ERPNext API error ({response.status_code}): {error_detail}")
                
                return response.json()
                
        except httpx.TimeoutException:
            raise ERPNextError("ERPNext API request timed out")
        except httpx.RequestError as e:
            raise ERPNextError(f"ERPNext API request failed: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to ERPNext instance.
        
        Returns:
            Connection test results
        """
        if not self.is_enabled:
            return {
                "connected": False,
                "error": "ERPNext integration not configured"
            }
        
        try:
            # Try to fetch a single customer to test connection
            response = await self._make_request(
                "GET", 
                self.endpoints["customers"],
                params={"limit": 1}
            )
            
            return {
                "connected": True,
                "message": "Successfully connected to ERPNext",
                "instance_url": self.base_url,
                "api_version": response.get("api_version", "Unknown")
            }
            
        except ERPNextError as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    async def sync_customer_to_erpnext(self, customer: Customer) -> Optional[str]:
        """
        Sync customer data to ERPNext.
        
        Args:
            customer: Customer model instance
            
        Returns:
            ERPNext customer ID if successful, None otherwise
            
        Raises:
            ERPNextError: If sync fails
        """
        if not self.is_enabled:
            return None
        
        try:
            # Check if customer already exists in ERPNext
            if customer.erpnext_customer_id:
                # Update existing customer
                customer_data = {
                    "customer_name": customer.customer_name,
                    "customer_type": "Company",
                    "territory": "All Territories",  # Default territory
                    "customer_group": "All Customer Groups",  # Default group
                    "payment_terms": customer.payment_terms,
                    "mobile_no": customer.phone,
                    "email_id": customer.email,
                }
                
                # Add custom fields
                if customer.customer_code:
                    customer_data["customer_code"] = customer.customer_code
                if customer.contact_person:
                    customer_data["primary_contact"] = customer.contact_person
                if customer.address:
                    customer_data["primary_address"] = customer.address
                
                endpoint = f"{self.endpoints['customers']}/{customer.erpnext_customer_id}"
                await self._make_request("PUT", endpoint, data=customer_data)
                
                return customer.erpnext_customer_id
            else:
                # Create new customer
                customer_data = {
                    "doctype": "Customer",
                    "customer_name": customer.customer_name,
                    "customer_code": customer.customer_code,
                    "customer_type": "Company",
                    "territory": "All Territories",
                    "customer_group": "All Customer Groups",
                    "payment_terms": customer.payment_terms,
                    "mobile_no": customer.phone,
                    "email_id": customer.email,
                }
                
                # Add custom fields
                if customer.contact_person:
                    customer_data["primary_contact"] = customer.contact_person
                if customer.address:
                    customer_data["primary_address"] = customer.address
                
                response = await self._make_request("POST", self.endpoints["customers"], data=customer_data)
                
                if "data" in response and "name" in response["data"]:
                    return response["data"]["name"]
                elif "message" in response and "name" in response["message"]:
                    return response["message"]["name"]
                
                return None
                
        except ERPNextError:
            raise
        except Exception as e:
            raise ERPNextError(f"Failed to sync customer to ERPNext: {str(e)}")
    
    async def sync_product_to_erpnext(self, product: Product) -> Optional[str]:
        """
        Sync product data to ERPNext as an Item.
        
        Args:
            product: Product model instance
            
        Returns:
            ERPNext item code if successful, None otherwise
        """
        if not self.is_enabled:
            return None
        
        try:
            # Check if item already exists in ERPNext
            if product.erpnext_item_code:
                # Update existing item
                item_data = {
                    "item_name": product.part_name,
                    "description": product.material_description or product.part_name,
                    "item_group": "Products",  # Default group
                    "stock_uom": product.unit_of_measure,
                    "standard_rate": product.standard_cost,
                    "is_sales_item": 1,
                    "is_purchase_item": 1,
                    "is_stock_item": 1,
                    "include_item_in_manufacturing": 1,
                }
                
                # Add custom fields
                if product.drawing_no:
                    item_data["drawing_no"] = product.drawing_no
                if product.material_code:
                    item_data["material_code"] = product.material_code
                if product.specifications:
                    item_data["specifications"] = json.dumps(product.specifications)
                
                endpoint = f"{self.endpoints['items']}/{product.erpnext_item_code}"
                await self._make_request("PUT", endpoint, data=item_data)
                
                return product.erpnext_item_code
            else:
                # Create new item
                item_data = {
                    "doctype": "Item",
                    "item_code": product.part_no,
                    "item_name": product.part_name,
                    "description": product.material_description or product.part_name,
                    "item_group": "Products",
                    "stock_uom": product.unit_of_measure,
                    "standard_rate": product.standard_cost,
                    "is_sales_item": 1,
                    "is_purchase_item": 1,
                    "is_stock_item": 1,
                    "include_item_in_manufacturing": 1,
                }
                
                # Add custom fields
                if product.drawing_no:
                    item_data["drawing_no"] = product.drawing_no
                if product.material_code:
                    item_data["material_code"] = product.material_code
                if product.specifications:
                    item_data["specifications"] = json.dumps(product.specifications)
                
                response = await self._make_request("POST", self.endpoints["items"], data=item_data)
                
                if "data" in response and "name" in response["data"]:
                    return response["data"]["name"]
                elif "message" in response and "name" in response["message"]:
                    return response["message"]["name"]
                
                return None
                
        except ERPNextError:
            raise
        except Exception as e:
            raise ERPNextError(f"Failed to sync product to ERPNext: {str(e)}")
    
    async def sync_sales_order_to_erpnext(self, requirement: CustomerRequirement, customer: Optional[Customer] = None) -> Optional[str]:
        """
        Sync customer requirement to ERPNext as a Sales Order.
        
        Args:
            requirement: CustomerRequirement model instance
            customer: Optional Customer model instance
            
        Returns:
            ERPNext sales order ID if successful, None otherwise
        """
        if not self.is_enabled:
            return None
        
        try:
            # Check if sales order already exists
            if requirement.erpnext_sales_order_id:
                # Update existing sales order (limited fields)
                sales_order_data = {
                    "delivery_date": requirement.due_date.isoformat(),
                    "status": self._map_requirement_status_to_erpnext(requirement.status),
                }
                
                endpoint = f"{self.endpoints['sales_orders']}/{requirement.erpnext_sales_order_id}"
                await self._make_request("PUT", endpoint, data=sales_order_data)
                
                return requirement.erpnext_sales_order_id
            else:
                # Create new sales order
                sales_order_data = {
                    "doctype": "Sales Order",
                    "naming_series": "SAL-ORD-.YYYY.-",
                    "customer": customer.erpnext_customer_id if customer and customer.erpnext_customer_id else requirement.customer_name,
                    "transaction_date": datetime.now().date().isoformat(),
                    "delivery_date": requirement.due_date.isoformat(),
                    "po_no": requirement.po_no,
                    "items": [
                        {
                            "item_code": requirement.product.erpnext_item_code or requirement.product.part_no,
                            "item_name": requirement.product.part_name,
                            "description": requirement.product.material_description or requirement.product.part_name,
                            "qty": requirement.po_quantity,
                            "rate": requirement.unit_price or requirement.product.standard_cost or 0,
                            "uom": requirement.product.unit_of_measure,
                            "delivery_date": requirement.due_date.isoformat(),
                        }
                    ],
                    "currency": "USD",  # Default currency
                    "selling_price_list": "Standard Selling",  # Default price list
                }
                
                # Add custom fields
                sales_order_data["custom_sale_no"] = requirement.sale_no
                if requirement.notes:
                    sales_order_data["remarks"] = requirement.notes
                
                response = await self._make_request("POST", self.endpoints["sales_orders"], data=sales_order_data)
                
                if "data" in response and "name" in response["data"]:
                    return response["data"]["name"]
                elif "message" in response and "name" in response["message"]:
                    return response["message"]["name"]
                
                return None
                
        except ERPNextError:
            raise
        except Exception as e:
            raise ERPNextError(f"Failed to sync sales order to ERPNext: {str(e)}")
    
    async def sync_work_order_to_erpnext(self, production_order: ProductionOrder) -> Optional[str]:
        """
        Sync production order to ERPNext as a Work Order.
        
        Args:
            production_order: ProductionOrder model instance
            
        Returns:
            ERPNext work order ID if successful, None otherwise
        """
        if not self.is_enabled:
            return None
        
        try:
            # Check if work order already exists
            if production_order.erpnext_work_order_id:
                # Update existing work order
                work_order_data = {
                    "qty": production_order.planned_quantity,
                    "produced_qty": production_order.produced_quantity,
                    "planned_start_date": production_order.start_date.isoformat() if production_order.start_date else None,
                    "planned_end_date": production_order.target_completion_date.isoformat(),
                    "actual_start_date": production_order.start_date.isoformat() if production_order.start_date else None,
                    "actual_end_date": production_order.actual_completion_date.isoformat() if production_order.actual_completion_date else None,
                    "status": self._map_production_status_to_erpnext(production_order.production_status),
                }
                
                endpoint = f"{self.endpoints['work_orders']}/{production_order.erpnext_work_order_id}"
                await self._make_request("PUT", endpoint, data=work_order_data)
                
                return production_order.erpnext_work_order_id
            else:
                # Create new work order
                work_order_data = {
                    "doctype": "Work Order",
                    "naming_series": "MFG-WO-.YYYY.-",
                    "production_item": production_order.product.erpnext_item_code or production_order.product.part_no,
                    "qty": production_order.planned_quantity,
                    "produced_qty": production_order.produced_quantity,
                    "company": "Your Company",  # Default company
                    "planned_start_date": production_order.start_date.isoformat() if production_order.start_date else datetime.now().date().isoformat(),
                    "planned_end_date": production_order.target_completion_date.isoformat(),
                    "priority": self._map_priority_to_erpnext(production_order.priority),
                    "status": self._map_production_status_to_erpnext(production_order.production_status),
                }
                
                # Add custom fields
                work_order_data["custom_production_order_no"] = production_order.production_order_no
                if production_order.production_notes:
                    work_order_data["remarks"] = production_order.production_notes
                
                response = await self._make_request("POST", self.endpoints["work_orders"], data=work_order_data)
                
                if "data" in response and "name" in response["data"]:
                    return response["data"]["name"]
                elif "message" in response and "name" in response["message"]:
                    return response["message"]["name"]
                
                return None
                
        except ERPNextError:
            raise
        except Exception as e:
            raise ERPNextError(f"Failed to sync work order to ERPNext: {str(e)}")
    
    def _map_requirement_status_to_erpnext(self, status: str) -> str:
        """Map customer requirement status to ERPNext sales order status."""
        mapping = {
            "pending": "Draft",
            "partial": "To Deliver and Bill",
            "completed": "Completed",
            "cancelled": "Cancelled"
        }
        return mapping.get(status, "Draft")
    
    def _map_production_status_to_erpnext(self, status: str) -> str:
        """Map production order status to ERPNext work order status."""
        mapping = {
            "pending": "Draft",
            "planned": "Not Started",
            "in_progress": "In Process",
            "completed": "Completed",
            "cancelled": "Cancelled",
            "on_hold": "Stopped"
        }
        return mapping.get(status, "Draft")
    
    def _map_priority_to_erpnext(self, priority: str) -> str:
        """Map priority to ERPNext priority levels."""
        mapping = {
            "low": "Low",
            "normal": "Medium",
            "high": "High",
            "urgent": "High"
        }
        return mapping.get(priority, "Medium")
    
    async def fetch_customers_from_erpnext(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch customers from ERPNext.
        
        Args:
            limit: Maximum number of customers to fetch
            
        Returns:
            List of customer data dictionaries
        """
        if not self.is_enabled:
            return []
        
        try:
            params = {
                "fields": ["name", "customer_name", "customer_code", "mobile_no", "email_id", "territory", "customer_group"],
                "limit": limit
            }
            
            response = await self._make_request("GET", self.endpoints["customers"], params=params)
            
            if "data" in response:
                return response["data"]
            
            return []
            
        except ERPNextError:
            raise
        except Exception as e:
            raise ERPNextError(f"Failed to fetch customers from ERPNext: {str(e)}")
    
    async def fetch_items_from_erpnext(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch items from ERPNext.
        
        Args:
            limit: Maximum number of items to fetch
            
        Returns:
            List of item data dictionaries
        """
        if not self.is_enabled:
            return []
        
        try:
            params = {
                "fields": ["name", "item_code", "item_name", "description", "stock_uom", "standard_rate", "item_group"],
                "filters": [["is_sales_item", "=", 1]],
                "limit": limit
            }
            
            response = await self._make_request("GET", self.endpoints["items"], params=params)
            
            if "data" in response:
                return response["data"]
            
            return []
            
        except ERPNextError:
            raise
        except Exception as e:
            raise ERPNextError(f"Failed to fetch items from ERPNext: {str(e)}")
    
    async def bulk_sync_to_erpnext(
        self, 
        customers: List[Customer] = None,
        products: List[Product] = None,
        requirements: List[CustomerRequirement] = None,
        production_orders: List[ProductionOrder] = None
    ) -> Dict[str, Any]:
        """
        Perform bulk synchronization to ERPNext.
        
        Args:
            customers: List of customers to sync
            products: List of products to sync
            requirements: List of customer requirements to sync
            production_orders: List of production orders to sync
            
        Returns:
            Sync results summary
        """
        if not self.is_enabled:
            return {"error": "ERPNext integration not enabled"}
        
        results = {
            "customers": {"synced": 0, "errors": []},
            "products": {"synced": 0, "errors": []},
            "sales_orders": {"synced": 0, "errors": []},
            "work_orders": {"synced": 0, "errors": []}
        }
        
        try:
            # Sync customers
            if customers:
                for customer in customers:
                    try:
                        erpnext_id = await self.sync_customer_to_erpnext(customer)
                        if erpnext_id:
                            results["customers"]["synced"] += 1
                    except Exception as e:
                        results["customers"]["errors"].append({
                            "customer_code": customer.customer_code,
                            "error": str(e)
                        })
            
            # Sync products
            if products:
                for product in products:
                    try:
                        erpnext_id = await self.sync_product_to_erpnext(product)
                        if erpnext_id:
                            results["products"]["synced"] += 1
                    except Exception as e:
                        results["products"]["errors"].append({
                            "part_no": product.part_no,
                            "error": str(e)
                        })
            
            # Sync customer requirements as sales orders
            if requirements:
                for requirement in requirements:
                    try:
                        erpnext_id = await self.sync_sales_order_to_erpnext(requirement)
                        if erpnext_id:
                            results["sales_orders"]["synced"] += 1
                    except Exception as e:
                        results["sales_orders"]["errors"].append({
                            "sale_no": requirement.sale_no,
                            "error": str(e)
                        })
            
            # Sync production orders as work orders
            if production_orders:
                for order in production_orders:
                    try:
                        erpnext_id = await self.sync_work_order_to_erpnext(order)
                        if erpnext_id:
                            results["work_orders"]["synced"] += 1
                    except Exception as e:
                        results["work_orders"]["errors"].append({
                            "production_order_no": order.production_order_no,
                            "error": str(e)
                        })
            
            return results
            
        except Exception as e:
            return {"error": f"Bulk sync failed: {str(e)}"}


# Global service instance
erpnext_service = ERPNextService()