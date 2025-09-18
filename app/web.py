"""
Web routes for serving frontend templates.

Handles authentication, dashboard, and main application pages.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_current_user_optional,
    get_current_active_user,
)
from app.models.user import User
from app.schemas.user import LoginRequest

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    """
    Redirect root to dashboard.
    """
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Login page.
    
    Args:
        request: HTTP request object
        current_user: Current user if authenticated
        
    Returns:
        HTMLResponse: Login page template
    """
    # Redirect to dashboard if already logged in
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse(
        "auth/login.html", 
        {"request": request}
    )


@router.get("/logout")
async def logout_page():
    """
    Logout page - redirects to login with logout message.
    """
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Main dashboard page.
    
    Args:
        request: HTTP request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        HTMLResponse: Dashboard template with data
    """
    # For demo purposes, use mock data to avoid database complexity
    dashboard_data = {
        "stats": {
            "total_orders": 42,
            "active_production": 15,
            "pending_deliveries": 8,
            "monthly_revenue": 125000.50
        },
        "recent_requirements": [
            {
                "sale_no": "SO-2024-001",
                "customer_name": "ABC Manufacturing",
                "product_part_name": "Motor Housing",
                "po_quantity": 100,
                "summary_status": "Complete"
            },
            {
                "sale_no": "SO-2024-002", 
                "customer_name": "XYZ Industries",
                "product_part_name": "Gear Assembly",
                "po_quantity": 50,
                "summary_status": "Pending"
            },
            {
                "sale_no": "SO-2024-003",
                "customer_name": "DEF Corporation",
                "product_part_name": "Steel Bracket",
                "po_quantity": 200,
                "summary_status": "Complete"
            }
        ],
        "recent_production": [
            {
                "production_order_no": "PO-2024-001",
                "product_part_name": "Motor Housing",
                "completion_percentage": 85
            },
            {
                "production_order_no": "PO-2024-002",
                "product_part_name": "Gear Assembly", 
                "completion_percentage": 45
            },
            {
                "production_order_no": "PO-2024-003",
                "product_part_name": "Steel Bracket",
                "completion_percentage": 100
            }
        ],
        "production_status": {
            "pending": 5,
            "in_progress": 10,
            "completed": 25,
            "on_hold": 2
        }
    }
    
    # Mock user data if no user is authenticated
    mock_user = {
        "username": "demo_user",
        "full_name": "Demo User",
        "department": {"name": "Administration"},
        "role": {"name": "Manager"}
    }
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user or mock_user,
            **dashboard_data
        }
    )


@router.get("/sales/customers", response_class=HTMLResponse)
async def customers_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Customers management page.
    """
    return templates.TemplateResponse(
        "sales/customers.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/sales/requirements", response_class=HTMLResponse)
async def requirements_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Customer requirements page.
    """
    return templates.TemplateResponse(
        "sales/requirements.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/sales/dashboard", response_class=HTMLResponse)
async def sales_dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Sales dashboard page.
    """
    return templates.TemplateResponse(
        "sales/dashboard.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/production/orders", response_class=HTMLResponse)
async def production_orders_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Production orders page.
    """
    return templates.TemplateResponse(
        "production/orders.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/production/tracking", response_class=HTMLResponse)
async def production_tracking_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Production tracking page.
    """
    return templates.TemplateResponse(
        "production/tracking.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/production/dashboard", response_class=HTMLResponse)
async def production_dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Production dashboard page.
    """
    return templates.TemplateResponse(
        "production/dashboard.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/products", response_class=HTMLResponse)
async def products_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Products list page - ATP Product Management.
    """
    return templates.TemplateResponse(
        "products/list.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "ATP Product Management"
        }
    )


@router.get("/products/create", response_class=HTMLResponse)
async def products_create_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Create product page - Add new ATP Product.
    """
    return templates.TemplateResponse(
        "products/create.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Create New Product"
        }
    )


@router.get("/products/lookup", response_class=HTMLResponse)
async def products_lookup_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Product lookup page - Search and explore ATP products.
    """
    return templates.TemplateResponse(
        "products/lookup.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Product Lookup"
        }
    )


@router.get("/excel/upload", response_class=HTMLResponse)
async def excel_upload_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Excel upload page.
    """
    return templates.TemplateResponse(
        "excel_upload.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/excel/download", response_class=HTMLResponse)
async def excel_download_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Excel download page.
    """
    return templates.TemplateResponse(
        "excel/download.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/excel/templates", response_class=HTMLResponse)
async def excel_templates_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Excel templates page.
    """
    return templates.TemplateResponse(
        "excel/templates.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/erpnext", response_class=HTMLResponse)
async def erpnext_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    ERPNext integration page.
    """
    return templates.TemplateResponse(
        "erpnext/sync.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    User management page (admin only).
    """
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    System settings page.
    """
    return templates.TemplateResponse(
        "settings/system.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    User profile page.
    """
    return templates.TemplateResponse(
        "auth/profile.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/help", response_class=HTMLResponse)
async def help_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Help and support page.
    """
    return templates.TemplateResponse(
        "help/index.html",
        {
            "request": request,
            "user": current_user
        }
    )


@router.get("/master-data/materials", response_class=HTMLResponse)
async def material_codes_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Material Code management page - Table view.
    """
    return templates.TemplateResponse(
        "master_data/material_codes_table.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Material Code Management"
        }
    )


@router.get("/master-data/materials/cards", response_class=HTMLResponse)
async def material_codes_cards_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Material Code management page - Card view (legacy).
    """
    return templates.TemplateResponse(
        "master_data/material_codes.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Material Code Management"
        }
    )


@router.get("/master-data/colors", response_class=HTMLResponse)
async def color_codes_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Color Code management page - Table view.
    """
    return templates.TemplateResponse(
        "master_data/color_codes_table.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Color Code Management"
        }
    )


@router.get("/master-data/colors/cards", response_class=HTMLResponse)
async def color_codes_cards_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Color Code management page - Card view (legacy).
    """
    return templates.TemplateResponse(
        "master_data/color_codes.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Color Code Management"
        }
    )


@router.get("/master-data/materials/create", response_class=HTMLResponse)
async def material_codes_create_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Create Material Code page.
    """
    return templates.TemplateResponse(
        "master_data/material_codes_create.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Create New Material Code"
        }
    )


@router.get("/master-data/materials/edit", response_class=HTMLResponse)
async def material_codes_edit_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Edit Material Code page.
    """
    return templates.TemplateResponse(
        "master_data/material_codes_edit.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Edit Material Code"
        }
    )


@router.get("/master-data/colors/create", response_class=HTMLResponse)
async def color_codes_create_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Create Color Code page.
    """
    return templates.TemplateResponse(
        "master_data/color_codes_create.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Create New Color Code"
        }
    )


@router.get("/master-data/colors/edit", response_class=HTMLResponse)
async def color_codes_edit_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Edit Color Code page.
    """
    return templates.TemplateResponse(
        "master_data/color_codes_edit.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Edit Color Code"
        }
    )


@router.get("/products/edit", response_class=HTMLResponse)
async def products_edit_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Edit Product page.
    """
    return templates.TemplateResponse(
        "products/edit.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Edit Product"
        }
    )