"""Copy the ready Module 1 index into Module 5 without opening the original."""
from pathlib import Path
import shutil


def main():
    assignment = Path(__file__).resolve().parent
    source = assignment.parents[1] / 'module_1/assignment/.rag_indexes/research_papers'
    target = assignment / '.rag_indexes/research_papers'
    if (target / '.index_ready').is_file():
        print(f'Reusing Module 5 index copy: {target}')
        return
    if target.exists():
        raise SystemExit('Incomplete Module 5 index copy exists; inspect it before retrying.')
    if not (source / '.index_ready').is_file():
        raise SystemExit('The existing Module 1 index is required; no re-embedding is performed.')
    shutil.copytree(source, target)
    print(f'Copied existing index to {target}')


if __name__ == '__main__':
    main()
