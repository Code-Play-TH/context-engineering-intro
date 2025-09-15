"""Create initial schema

Revision ID: 0001
Revises: 
Create Date: 2024-12-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables for the Factory ERP system."""
    
    # Create departments table
    op.create_table('department',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_department_code'), 'department', ['code'], unique=False)
    op.create_index(op.f('ix_department_name'), 'department', ['name'], unique=False)

    # Create role table
    op.create_table('role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('permissions_json', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['department.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_code'), 'role', ['code'], unique=False)
    op.create_index(op.f('ix_role_name'), 'role', ['name'], unique=False)

    # Create user table
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['department.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)

    # Create product table
    op.create_table('product',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('part_no', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('part_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('drawing_no', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('material_code', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('material_description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('unit_of_measure', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('standard_cost', sa.Float(), nullable=True),
        sa.Column('production_steps_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('erpnext_item_code', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('specifications_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('part_no')
    )
    op.create_index(op.f('ix_product_part_no'), 'product', ['part_no'], unique=False)

    # Create production step table
    op.create_table('productionstep',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('estimated_time_minutes', sa.Integer(), nullable=True),
        sa.Column('machine_required', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('skill_level', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create customer table
    op.create_table('customer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('customer_code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('customer_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('contact_person', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('address', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('payment_terms', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('erpnext_customer_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_code')
    )
    op.create_index(op.f('ix_customer_customer_code'), 'customer', ['customer_code'], unique=False)
    op.create_index(op.f('ix_customer_customer_name'), 'customer', ['customer_name'], unique=False)

    # Create customer requirement table
    op.create_table('customerrequirement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('sale_no', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('po_no', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('customer_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('po_quantity', sa.Integer(), nullable=False),
        sa.Column('delivered_quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('sales_person_id', sa.Integer(), nullable=False),
        sa.Column('erpnext_sales_order_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.ForeignKeyConstraint(['sales_person_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customerrequirement_po_no'), 'customerrequirement', ['po_no'], unique=False)
    op.create_index(op.f('ix_customerrequirement_sale_no'), 'customerrequirement', ['sale_no'], unique=False)

    # Create production order table
    op.create_table('productionorder',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('production_order_no', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('customer_requirement_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('planned_quantity', sa.Integer(), nullable=False),
        sa.Column('produced_quantity', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('target_completion_date', sa.DateTime(), nullable=False),
        sa.Column('actual_completion_date', sa.DateTime(), nullable=True),
        sa.Column('production_status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('priority', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=False),
        sa.Column('erpnext_work_order_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('production_notes', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['customer_requirement_id'], ['customerrequirement.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('production_order_no')
    )
    op.create_index(op.f('ix_productionorder_production_order_no'), 'productionorder', ['production_order_no'], unique=False)

    # Create production tracking table
    op.create_table('productiontracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('production_order_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('quantity_produced', sa.Integer(), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('machine_used', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('quality_check_passed', sa.Boolean(), nullable=False),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['production_order_id'], ['productionorder.id'], ),
        sa.ForeignKeyConstraint(['step_id'], ['productionstep.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create supplier table
    op.create_table('supplier',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('supplier_code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('supplier_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('contact_person', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('address', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('payment_terms', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('erpnext_supplier_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supplier_code')
    )
    op.create_index(op.f('ix_supplier_supplier_code'), 'supplier', ['supplier_code'], unique=False)
    op.create_index(op.f('ix_supplier_supplier_name'), 'supplier', ['supplier_name'], unique=False)

    # Create purchase order table
    op.create_table('purchaseorder',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('po_number', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('order_date', sa.DateTime(), nullable=False),
        sa.Column('expected_delivery_date', sa.DateTime(), nullable=True),
        sa.Column('actual_delivery_date', sa.DateTime(), nullable=True),
        sa.Column('erpnext_purchase_order_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('po_number')
    )
    op.create_index(op.f('ix_purchaseorder_po_number'), 'purchaseorder', ['po_number'], unique=False)

    # Create purchase order item table
    op.create_table('purchaseorderitem',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('received_quantity', sa.Integer(), nullable=False),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchaseorder.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create audit log table
    op.create_table('auditlog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('table_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('old_values_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('new_values_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('ip_address', sqlmodel.sql.sqltypes.AutoString(length=45), nullable=True),
        sa.Column('user_agent', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auditlog_action'), 'auditlog', ['action'], unique=False)
    op.create_index(op.f('ix_auditlog_record_id'), 'auditlog', ['record_id'], unique=False)
    op.create_index(op.f('ix_auditlog_table_name'), 'auditlog', ['table_name'], unique=False)

    # Create ERPNext sync log table
    op.create_table('erpnextsynclog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('entity_type', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('erpnext_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('sync_action', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('sync_status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('error_message', sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('synced_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_erpnextsynclog_entity_id'), 'erpnextsynclog', ['entity_id'], unique=False)
    op.create_index(op.f('ix_erpnextsynclog_entity_type'), 'erpnextsynclog', ['entity_type'], unique=False)
    op.create_index(op.f('ix_erpnextsynclog_sync_status'), 'erpnextsynclog', ['sync_status'], unique=False)

    # Create Excel operation table
    op.create_table('exceloperation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('operation_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('file_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('file_path', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('records_processed', sa.Integer(), nullable=False),
        sa.Column('records_successful', sa.Integer(), nullable=False),
        sa.Column('records_failed', sa.Integer(), nullable=False),
        sa.Column('errors_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exceloperation_operation_type'), 'exceloperation', ['operation_type'], unique=False)
    op.create_index(op.f('ix_exceloperation_status'), 'exceloperation', ['status'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('exceloperation')
    op.drop_table('erpnextsynclog')
    op.drop_table('auditlog')
    op.drop_table('purchaseorderitem')
    op.drop_table('purchaseorder')
    op.drop_table('supplier')
    op.drop_table('productiontracking')
    op.drop_table('productionorder')
    op.drop_table('customerrequirement')
    op.drop_table('customer')
    op.drop_table('productionstep')
    op.drop_table('product')
    op.drop_table('user')
    op.drop_table('role')
    op.drop_table('department')