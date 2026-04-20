def calculate_risk_level(probability: str, impact: str) -> str:
    matrix = {
        ('High', 'High'): 'Critical',
        ('High', 'Medium'): 'High',
        ('High', 'Low'): 'Medium',
        ('Medium', 'High'): 'High',
        ('Medium', 'Medium'): 'Medium',
        ('Medium', 'Low'): 'Low',
        ('Low', 'High'): 'Medium',
        ('Low', 'Medium'): 'Low',
        ('Low', 'Low'): 'Low',
    }
    return matrix.get((probability, impact), 'Medium')
