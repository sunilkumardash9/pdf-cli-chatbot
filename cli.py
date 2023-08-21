import argparse
from app import (
    add_text_to_collection, 
    get_answer, 
    verify_pdf_path, 
    clear_coll
  )

# path = "/home/sunil/Downloads/fess107.pdf"

def main():
    parser = argparse.ArgumentParser(description="PDF Processing CLI Tool")
    parser.add_argument("-f", "--file", help="Path to the input PDF file")
    parser.add_argument("-v", "--value",default=200, type=int, help="Optional integer value for no. words in a single chunk")
    parser.add_argument("-q", "--question", type = str ,help="Ask a question")
    parser.add_argument("-c", "--clear", type = bool, help = "Clear existing collection data")
    parser.add_argument('-n', "--number", type = int, default=1, help = "Number of results to be fetched from collection")

    args = parser.parse_args()
    
    if args.file is not None:
        verify_pdf_path(args.file)
        confirmation = add_text_to_collection(file = args.file, word = args.value)
        print(confirmation)

    if args.question is not None:
        if args.number:
            n = args.number
        else:
            n = 1
        answer = get_answer(args.question, n = n)
        print("Answer:", answer)

    if args.clear:
        clear_coll()
        return "Current collection cleared successfully"



if __name__ == "__main__":
    main()
