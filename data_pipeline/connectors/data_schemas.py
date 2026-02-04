"""
Schemas de dados para validação dos datasets da ANATEL.
Define a estrutura esperada para cada tipo de dataset.
"""

from typing import Any

# Schema para dados de backhaul
BACKHAUL_SCHEMA = {
    'required_fields': [
        'id',
        'municipio',
        'uf',
        'operadora',
        'latitude',
        'longitude',
        'frequencia',
        'capacidade_mbps'
    ],
    'optional_fields': [
        'tecnologia',
        'data_instalacao',
        'status'
    ],
    'field_types': {
        'id': 'string',
        'municipio': 'string',
        'uf': 'string',
        'operadora': 'string',
        'latitude': 'float',
        'longitude': 'float',
        'frequencia': 'string',
        'capacidade_mbps': 'float',
        'tecnologia': 'string',
        'data_instalacao': 'string',
        'status': 'string'
    }
}

# Schema para dados de estações
ESTACOES_SCHEMA = {
    'required_fields': [
        'id',
        'municipio',
        'uf',
        'operadora',
        'tecnologia',
        'latitude',
        'longitude'
    ],
    'optional_fields': [
        'data_ativacao',
        'status',
        'tipo_estacao'
    ],
    'field_types': {
        'id': 'string',
        'municipio': 'string',
        'uf': 'string',
        'operadora': 'string',
        'tecnologia': 'string',
        'latitude': 'float',
        'longitude': 'float',
        'data_ativacao': 'string',
        'status': 'string',
        'tipo_estacao': 'string'
    }
}

# Schema para dados de acesso fixo
ACESSO_FIXO_SCHEMA = {
    'required_fields': [
        'municipio',
        'uf',
        'quantidade',
        'velocidade',
        'tecnologia'
    ],
    'optional_fields': [
        'operadora',
        'ano',
        'mes'
    ],
    'field_types': {
        'municipio': 'string',
        'uf': 'string',
        'quantidade': 'int',
        'velocidade': 'string',
        'tecnologia': 'string',
        'operadora': 'string',
        'ano': 'int',
        'mes': 'int'
    }
}

# Mapeamento de schemas por tipo de dataset
SCHEMAS = {
    'backhaul': BACKHAUL_SCHEMA,
    'estacoes': ESTACOES_SCHEMA,
    'acesso_fixo': ACESSO_FIXO_SCHEMA
}


def get_schema(dataset_type: str) -> dict[str, Any]:
    """
    Retorna o schema para um tipo de dataset.
    
    Args:
        dataset_type: Tipo do dataset ('backhaul', 'estacoes', 'acesso_fixo')
        
    Returns:
        Dict contendo o schema do dataset
    """
    return SCHEMAS.get(dataset_type, {})


def validate_dataset(df, dataset_type: str) -> tuple[bool, list[str]]:
    """
    Valida se um DataFrame atende ao schema esperado.
    
    Args:
        df: DataFrame pandas a ser validado
        dataset_type: Tipo do dataset
        
    Returns:
        Tupla (is_valid, errors) onde is_valid é booleano e errors é lista de mensagens
    """
    schema = get_schema(dataset_type)
    
    if not schema:
        return False, [f"Schema desconhecido para tipo: {dataset_type}"]
    
    errors = []
    
    # Verificar campos obrigatórios
    required_fields = schema.get('required_fields', [])
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    if missing_fields:
        errors.append(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")
    
    # Se houver campos faltando, já retorna falso
    if errors:
        return False, errors
    
    # Validação bem-sucedida
    return True, []
