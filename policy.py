from typing import Dict, List


def make_advice(state: Dict) -> List[str]:
    tips = []

    # численный перевес на миникарте рядом ( по кластеру )
    cluster = state.get('enemy_max_cluster', 0)
    enemies = state.get('enemy_count', 0)
    allies = state.get('ally_count', 0)

    if cluster >= 3:
        tips.append('⚠ Рядом плотный вражеский кластер: не пикать, держи дистанцию')
    if enemies > allies + 2:
        tips.append('↩ Фланг слабее: откатись к укрытию/соединись с командой')
    if state.get('sixth_sense'):
        tips.append('💡 Засвет! Меняй позицию/ломай прострелы 5–7 сек')

    hp = state.get('hp')
    if hp is not None and hp < 400:
        tips.append('🧨 Мало ХП: играй от инфы и чужих стволов')

    if not tips:
        tips.append('✅ Нормально: аккуратно трейдь и контролируй перекрёстки')
    return tips
