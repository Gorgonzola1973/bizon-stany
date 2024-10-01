import streamlit as st
import json
import base64
import locale
import sys
import subprocess

# Pokus o nastavení locale, s fallbackem na výchozí nastavení
try:
    locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_NUMERIC, '')  # Použije výchozí systémové nastavení
    except locale.Error:
        pass  # Pokud ani to nefunguje, použijeme výchozí Python zpracování

JSON_FILE_PATH = 'data.json'


def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    json_string = json.dumps(data, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(json_string.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="updated_data.json">Stáhnout aktualizovaný JSON</a>'
    return href


def parse_price(price_str):
    try:
        return float(price_str.replace(',', '.'))
    except ValueError:
        return 0.0


def format_price(price_float):
    return f"{price_float:.2f}"


def edit_value(key, value, prefix=''):
    if isinstance(value, dict):
        st.write(f"{key}:")
        for k, v in value.items():
            value[k] = edit_value(k, v, f"{prefix}_{key}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            value[i] = edit_value(f"{key}[{i}]", item, f"{prefix}_{key}_{i}")
    elif isinstance(value, bool):
        return st.checkbox(key, value, key=f"{prefix}_{key}")
    elif isinstance(value, (int, float)):
        return st.number_input(key, value=value, format="%.2f" if isinstance(value, float) else "%d",
                               key=f"{prefix}_{key}")
    else:
        return st.text_input(key, str(value), key=f"{prefix}_{key}")
    return value


def main():
    st.title('JSON Editor pro Týpí')

    data = load_json(JSON_FILE_PATH)

    # Vytvoření postranního panelu pro navigaci
    st.sidebar.title("Navigace")
    main_section = st.sidebar.radio("Hlavní sekce", ["Obecné konfigurace", "Specifické konfigurace"])

    if main_section == "Obecné konfigurace":
        selected_config = st.sidebar.selectbox("Vyberte konfiguraci",
                                               ['config', 'form', 'strings', 'currency', 'base', 'dph'])
        st.header(f"Editace: {selected_config}")
        data[selected_config] = edit_value(selected_config, data[selected_config])

    else:  # Specifické konfigurace
        sizes = data['base']['items']
        selected_size = st.sidebar.selectbox(
            "Vyberte velikost týpí",
            options=[size['value'] for size in sizes],
            format_func=lambda x: next(size['name']['cs'] for size in sizes if size['value'] == x)
        )

        if str(selected_size) in data['variables']:
            variables = data['variables'][str(selected_size)]

            section_names = {variables[key]['name']['cs']: key for key in variables.keys() if
                             'name' in variables[key] and 'cs' in variables[key]['name']}

            selected_section_name = st.sidebar.selectbox("Vyberte sekci", list(section_names.keys()))
            selected_section = section_names[selected_section_name]

            st.header(f"Editace: Týpí {selected_size}m - {selected_section_name}")
            data['variables'][str(selected_size)][selected_section] = edit_value(
                selected_section,
                data['variables'][str(selected_size)][selected_section],
                f"variables_{selected_size}"
            )
        else:
            st.warning(f"Pro velikost {selected_size}m nejsou k dispozici žádné specifické konfigurace.")

    if st.sidebar.button('Uložit změny', key='save_button'):
        href = save_json(data, JSON_FILE_PATH)
        st.sidebar.success('Data byla úspěšně uložena do souboru.')
        st.sidebar.markdown(href, unsafe_allow_html=True)


if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        file_path = sys.argv[0]
        subprocess.run(["streamlit", "run", file_path])