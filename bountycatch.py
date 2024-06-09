import argparse
import redis
import os

class DataStore:
    def __init__(self, host='localhost', port=6379, db=0):
        self.r = redis.Redis(host=host, port=port, db=db)

    def add_domain(self, project, domain):
        return self.r.sadd(project, domain)

    def get_domains(self, project):
        return self.r.smembers(project)

    def deduplicate(self, project):
        pass

    def delete_project(self, project):
        return self.r.delete(project)
    
    def project_exists(self, project):
        return self.r.exists(project)

    def count_domains(self, project):
        return self.r.scard(project)

class Project:
    def __init__(self, datastore, name):
        self.datastore = datastore
        self.name = name

    def add_domains_from_file(self, filename):
        if not os.path.exists(filename):
            print("File {} does not exist.".format(filename))
            return
        with open(filename, 'r') as file:
            total_domains = 0
            new_domains = 0
            for line in file:
                domain = line.strip()
                if domain:
                    added = self.datastore.add_domain(self.name, domain)
                    new_domains += added
                total_domains += 1 if domain else 0
            duplicate_domains = total_domains - new_domains
            if total_domains > 0:
                duplicate_percentage = (duplicate_domains / total_domains) * 100
            else:
                duplicate_percentage = 0
            print("{} out of {} domains were duplicates ({:.2f}%).".format(duplicate_domains, total_domains, duplicate_percentage))

    def get_domains(self):
        return self.datastore.get_domains(self.name)
    
    def count_domains(self):
        if not self.datastore.project_exists(self.name):
            print(f"Error: Project '{self.name}' does not exist.")
            return
        count = self.datastore.count_domains(self.name)
        print(f"There are {count} domains in the project '{self.name}'.")

    def delete(self):
        print(f"Attempting to delete project '{self.name}'...")
        deleted_count = self.datastore.delete_project(self.name)
        if deleted_count == 0:
            print(f"No such project '{self.name}' to delete.")
        else:
            print(f"Project '{self.name}' deleted successfully.")

def main():
    parser = argparse.ArgumentParser(description="Manage bug bounty targets")
    parser.add_argument('project', help='The project name')
    subparsers = parser.add_subparsers(dest='operation', help='Operation to perform')

    # Add subdomains operation
    add_parser = subparsers.add_parser('add', help='To add subdomains for a project')
    add_parser.add_argument('file', help='The file containing domains')

    # Show all subdomains operation
    showall_parser = subparsers.add_parser('showall', help='To display the current project\'s subdomains')

    # Print only matched domain operation
    print_parser = subparsers.add_parser('print', help='To Print only matched domain')
    print_parser.add_argument('-d', '--domain', help='Print only matched domain')

    # Count subdomains operation
    count_parser = subparsers.add_parser('count', help='To count the number of subdomains for the current project')

    # Remove project operation
    remove_parser = subparsers.add_parser('remove', help='To remove a specific project')

    # Remove specific line operation
    remove_domain_parser = subparsers.add_parser('removedomain', help='To remove a specific line in a project')
    remove_domain_parser.add_argument('-d', '--domain', required=True, help='Domain to be removed')

    args = parser.parse_args()

    datastore = DataStore()
    project = Project(datastore, args.project)

    if args.operation == 'add':
        project.add_domains_from_file(args.file)
    elif args.operation == 'showall':
        domains = project.get_domains()
        sorted_domains = sorted(domain.decode('utf-8') for domain in domains)
        for domain in sorted_domains:
            print(domain)
    elif args.operation == 'print':
        if args.domain:
            domains = project.get_domains()
            matched_domains = sorted([d.decode('utf-8') for d in domains if args.domain in d.decode('utf-8')])
            if matched_domains:
                for domain in matched_domains:
                    print(domain)
            else:
                print(f"No matching domain found for '{args.domain}'.")
    elif args.operation == 'count':
        project.count_domains()
    elif args.operation == 'remove':
        project.delete()
    elif args.operation == 'removedomain':
        print(f"Removing specific domain '{args.domain}' from the project '{args.project}'...")
        removed = datastore.r.srem(args.project, args.domain)
        if removed == 0:
            print(f"No such domain '{args.domain}' in project '{args.project}'.")
        else:
            print(f"Domain '{args.domain}' removed successfully from project '{args.project}'.")
    else:
        print(f"Invalid operation: {args.operation}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")


# To add subdomains for a project:
# python3 bountycatch.py xyz.com add xyz_subdomains.txt

# To display the current project's subdomains:
# python3 bountycatch.py xyz.com showall

# To Print only matched domain:
# python3 bountycatch.py xyz.com print -d github.com

# To count the number of subdomains for the current project:
# python3 bountycatch.py xyz.com count

# To remove a specific project:
# python3 bountycatch.py xyz.com remove

# To remove a specific line in a project:
# python3 bountycatch.py xyz.com removedomain -d github.com
