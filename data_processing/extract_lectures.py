import pdfplumber
import os
import re

pdf_file = 'data/sources/liste_emploi_du_temps_examen_premiere_annee.pdf'
output_md = 'data/structured/lectures_list.md'

branches_data = {}

with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        
        # Look for "Classe : <Branch>"
        match = re.search(r"Classe\s*:\s*([A-Z0-9\s]+)", text)
        if match:
            branch = match.group(1).strip()
            # Extract subjects from the table
            table = page.extract_table()
            subjects = set()
            if table:
                for row in table:
                    for cell in row:
                        if cell:
                            # Clean up and ignore dates/headers
                            cell_cleaned = cell.strip()
                            if cell_cleaned and not re.search(r'\d{2}/\d{2}', cell_cleaned) and cell_cleaned not in ['Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Lundi', 'TP Topographie', '-']:
                                # it's likely a subject
                                subjects.add(cell_cleaned)
            
            # Additional clean up for common non-subjects
            ignore_list = ['Mardi 05/10', 'Mercredi 06/10', 'Jeudi 07/10', 'Vendredi 08/10', 'Lundi 11/10', 'Mardi 12/10', 'Mercredi 13/10', 'Jeudi 14/10', 'Le Recteur,', 'Mardi 22/06']
            # Filter subjects
            clean_subjects = []
            for subj in subjects:
                subj = subj.replace('\n', ' ').strip()
                if subj and not any(ign in subj for ign in ignore_list) and not 'Recteur' in subj and not 'Professeur' in subj and not 'Classe' in subj and not 'INSTITUT' in subj and not 'AMBATOMARO' in subj:
                    clean_subjects.append(subj)
            
            # Remove any empty or weird ones
            final_subjects = [s for s in clean_subjects if len(s) > 2]
            branches_data[branch] = sorted(list(set(final_subjects)))

with open(output_md, 'w', encoding='utf-8') as f:
    f.write("# Liste des matières par filière (Première année)\n\n")
    for branch, subjects in branches_data.items():
        f.write(f"## Filière : {branch}\n\n")
        f.write("**Liste des matières enseignables / évaluées :**\n\n")
        for subj in subjects:
            f.write(f"- {subj}\n")
        f.write("\n")

print(f"Extraction terminee. Resultats dans {output_md}")
