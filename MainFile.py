import streamlit as st
import PyPDF2
from MongoDBFunctions import MongoDB
from GeminiFunctions import GenerativeFunction

gemini = GenerativeFunction()

mongoDB = MongoDB()

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Main Function
def main_old():
    st.title("Automation Generator")

    mongoDB.search_bar()

    domain = st.text_input("Select Domain")
    extra_info = st.text_area("Additional Information")
    pdf_file = st.file_uploader("Upload PDF", type="pdf")

    if pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)
        summary = gemini.gemini_summarize(pdf_text, domain, extra_info)

        if summary:
            st.subheader("Summary")
            st.write(summary)

            block_diagram = gemini.gemini_generate_block_diagram(summary, domain, extra_info)
            st.subheader("Block Diagram")
            st.markdown(f"```\n{block_diagram}\n```")

            script = gemini.gemini_generate_script(summary, domain, extra_info)
            st.subheader("Automation Script")
            st.code(script, language='python')

            unit_tests = gemini.gemini_generate_unit_tests(summary, script, domain, extra_info)
            st.subheader("Unit Test Script")
            st.code(unit_tests, language='python')

            prerequisites = gemini.gemini_generate_prerequisites(summary, domain, extra_info)
            st.subheader("Prerequisites")
            st.write(prerequisites)

            if st.button("Save to Details to Database"):
                mongoDB.add_solution_to_mongodb(summary, script, block_diagram, prerequisites, domain, extra_info)
# Main Function
def main():
    st.title("Automation Generator")

    # Display search bar to search the solutions
    mongoDB.search_bar()

    # Input for domain and extra information
    domain = st.text_input("Select Domain")
    extra_info = st.text_area("Additional Information")
    pdf_file = st.file_uploader("Upload PDF", type="pdf")

    # Process the uploaded PDF file
    if pdf_file:
        # Extract text from the PDF
        pdf_text = extract_text_from_pdf(pdf_file)

        # Generate summary from the text
        summary = gemini.gemini_summarize(pdf_text, domain, extra_info)

        if summary:
            st.subheader("Summary")
            st.write(summary)

            # Generate block diagram
            block_diagram = gemini.gemini_generate_block_diagram(summary, domain, extra_info)
            st.subheader("Block Diagram")
            st.markdown(f"```\n{block_diagram}\n```")

            # Generate automation script and unit test
            script = gemini.gemini_generate_script(summary, domain, extra_info)
            unit_tests = gemini.gemini_generate_unit_tests(summary, script, domain, extra_info)

            # Create two columns for parallel display
            col1, col2 = st.columns(2)

            # Display the automation script in the first column
            with col1:
                st.subheader("Automation Script")
                st.code(script, language='python')

            # Display the unit test in the second column
            with col2:
                st.subheader("Unit Test Script")
                st.code(unit_tests, language='python')

            # Generate prerequisites
            prerequisites = gemini.gemini_generate_prerequisites(summary, domain, extra_info)
            st.subheader("Prerequisites")
            st.write(prerequisites)

            # Button to save the solution to the database
            if st.button("Save Details to Database"):
                mongoDB.add_solution_to_mongodb(summary, script, block_diagram, prerequisites, domain, extra_info)

if __name__ == '__main__':
    #mongoDB.create_search_index() # Need to run only First Time
    main()