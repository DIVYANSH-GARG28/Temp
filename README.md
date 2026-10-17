# connectED - AI-Powered Alumni Knowledge Graph

## 1. Project Overview

connectED is an AI-powered professional networking platform
that connects students with alumni, faculty, recruiters,
and professionals for mentorship, career guidance, and collaboration.

This module uses a Knowledge Graph to represent people,
skills, companies, and their relationships.

## 2. Problem Statement

Students often struggle to find relevant alumni who can
guide them toward their career goals.

A Knowledge Graph helps organize professional information
and discover useful connections between students and alumni.

## 3. Technologies Used

- Python
- NetworkX
- JSON
- Python unittest

## 4. Main Features

- Build a graph of students, alumni, skills, and companies.
- Find alumni with a particular skill.
- Display alumni professional details.
- Identify a student's existing skills.
- Export the Knowledge Graph to JSON.
- Test core functions automatically.

## 5. Project Structure

connectED/
- knowledge_graph.py
- sample_data.py
- test_knowledge_graph.py
- README.md
- knowledge_graph.json (generated when the program runs)

## 6. Installation

Install Python and then install NetworkX:

    python -m pip install networkx

## 7. Run the Project

Run the Knowledge Graph:

    python knowledge_graph.py

Run the tests:

    python -m unittest test_knowledge_graph.py -v

## 8. Sample Demonstration

The sample dataset includes:

- Student: Aarav
- Alumni: Riya and Kabir
- Skills: Python, Machine Learning, and SQL
- Companies: Google and Microsoft

The system can find alumni who have Python or
Machine Learning skills.

## 9. Future Improvements

- Add more students and alumni.
- Include mentorship and career-goal relationships.
- Connect the graph to a real database.
- Integrate the graph with a recommendation system.
- Build an API for the frontend.

## 10. Data Disclaimer

The included people and professional details are fictional
demonstration data. They do not represent verified real-world records