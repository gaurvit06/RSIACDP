import networkx as nx
from sqlalchemy.orm import Session

from app.models.case import Case

from app.models.case_phone import CasePhone
from app.models.phone import Phone

from app.models.case_email import CaseEmail
from app.models.email import Email

from app.models.case_domain import CaseDomain
from app.models.domain import Domain

from app.models.case_upi import CaseUPI
from app.models.upi import UPI


def build_investigation_graph(db: Session) -> nx.Graph:
    """
    Build an investigation graph from existing cases and shared entities.

    Nodes:
        case:<case_id>
        phone:<phone_id>
        email:<email_id>
        domain:<domain_id>
        upi:<upi_id>

    Edges:
        A case is connected to every entity found in that case.

    Shared entities therefore connect multiple cases together.
    """

    graph = nx.Graph()

    # Add case nodes
    cases = db.query(Case).all()

    for case in cases:
        graph.add_node(
            f"case:{case.id}",
            node_type="case",
            case_id=str(case.id),
        )

    # Connect cases to phones
    phone_links = (
        db.query(CasePhone, Phone)
        .join(
            Phone,
            Phone.id == CasePhone.phone_id
        )
        .all()
    )

    for case_phone, phone in phone_links:
        case_node = f"case:{case_phone.case_id}"
        phone_node = f"phone:{phone.id}"

        graph.add_node(
            phone_node,
            node_type="phone",
            value=phone.normalized_number,
        )

        graph.add_edge(
            case_node,
            phone_node,
            relationship="contains_phone",
        )

    # Connect cases to emails
    email_links = (
        db.query(CaseEmail, Email)
        .join(
            Email,
            Email.id == CaseEmail.email_id
        )
        .all()
    )

    for case_email, email in email_links:
        case_node = f"case:{case_email.case_id}"
        email_node = f"email:{email.id}"

        graph.add_node(
            email_node,
            node_type="email",
            value=email.normalized_address,
        )

        graph.add_edge(
            case_node,
            email_node,
            relationship="contains_email",
        )

    # Connect cases to domains
    domain_links = (
        db.query(CaseDomain, Domain)
        .join(
            Domain,
            Domain.id == CaseDomain.domain_id
        )
        .all()
    )

    for case_domain, domain in domain_links:
        case_node = f"case:{case_domain.case_id}"
        domain_node = f"domain:{domain.id}"

        graph.add_node(
            domain_node,
            node_type="domain",
            value=domain.normalized_domain,
        )

        graph.add_edge(
            case_node,
            domain_node,
            relationship="contains_domain",
        )

    # Connect cases to UPI IDs
    upi_links = (
        db.query(CaseUPI, UPI)
        .join(
            UPI,
            UPI.id == CaseUPI.upi_id
        )
        .all()
    )

    for case_upi, upi in upi_links:
        case_node = f"case:{case_upi.case_id}"
        upi_node = f"upi:{upi.id}"

        graph.add_node(
            upi_node,
            node_type="upi",
            value=upi.normalized_upi,
        )

        graph.add_edge(
            case_node,
            upi_node,
            relationship="contains_upi",
        )

    return graph

def find_connected_case_groups(
    graph: nx.Graph
) -> list[list[str]]:
    """
    Find groups of cases connected through shared entities.

    Only case nodes are returned.
    Entity nodes such as phones, emails, domains, and UPI IDs
    are used internally to establish the connections.
    """

    case_groups = []

    for component in nx.connected_components(graph):
        case_nodes = [
            node
            for node in component
            if node.startswith("case:")
        ]

        if len(case_nodes) >= 2:
            case_ids = [
                node.replace("case:", "")
                for node in case_nodes
            ]

            case_groups.append(case_ids)

    return case_groups