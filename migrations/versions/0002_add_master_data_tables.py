"""Add master data tables for Material and Color codes

Revision ID: 0002_add_master_data_tables
Revises: 0001
Create Date: 2024-12-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '0002_add_master_data_tables'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add MaterialCode and ColorCode master data tables."""
    
    # Create MaterialCode table
    op.create_table('materialcode',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('material_code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('material_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('material_category', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('material_type', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('density', sa.Float(), nullable=True),
        sa.Column('melting_point', sa.Float(), nullable=True),
        sa.Column('hardness', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('standard_thickness', sa.Float(), nullable=True),
        sa.Column('unit_weight', sa.Float(), nullable=True),
        sa.Column('cost_per_unit', sa.Float(), nullable=True),
        sa.Column('primary_supplier', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('supplier_code', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('tensile_strength', sa.Float(), nullable=True),
        sa.Column('yield_strength', sa.Float(), nullable=True),
        sa.Column('surface_finish', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('specifications', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('handling_notes', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('material_code')
    )
    op.create_index(op.f('ix_materialcode_material_code'), 'materialcode', ['material_code'], unique=False)
    
    # Create ColorCode table
    op.create_table('colorcode',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('color_code', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('color_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('hex_value', sqlmodel.sql.sqltypes.AutoString(length=7), nullable=True),
        sa.Column('rgb_value', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column('cmyk_value', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column('pantone_code', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column('ral_code', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column('ncs_code', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column('color_family', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('color_intensity', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('finish_type', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('paint_type', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('cure_temperature', sa.Float(), nullable=True),
        sa.Column('cure_time_minutes', sa.Integer(), nullable=True),
        sa.Column('cost_per_liter', sa.Float(), nullable=True),
        sa.Column('coverage_per_liter', sa.Float(), nullable=True),
        sa.Column('supplier_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('supplier_product_code', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('color_tolerance', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('uv_resistance', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('weather_resistance', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('application_notes', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('color_code')
    )
    op.create_index(op.f('ix_colorcode_color_code'), 'colorcode', ['color_code'], unique=False)
    
    # Add foreign key columns to product table
    op.add_column('product', sa.Column('material_code_id', sa.Integer(), nullable=True))
    op.add_column('product', sa.Column('color_code_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'product', 'materialcode', ['material_code_id'], ['id'])
    op.create_foreign_key(None, 'product', 'colorcode', ['color_code_id'], ['id'])


def downgrade() -> None:
    """Remove MaterialCode and ColorCode master data tables."""
    
    # Remove foreign keys and columns from product table
    op.drop_constraint(None, 'product', type_='foreignkey')
    op.drop_column('product', 'color_code_id')
    op.drop_column('product', 'material_code_id')
    
    # Drop tables
    op.drop_index(op.f('ix_colorcode_color_code'), table_name='colorcode')
    op.drop_table('colorcode')
    op.drop_index(op.f('ix_materialcode_material_code'), table_name='materialcode')
    op.drop_table('materialcode')