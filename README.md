# Kubernetes Policy-as-Code using Kyverno and OPA Gatekeeper 

This project involves using a deliberately vulnerable bank application, VULN-BANK by [Commando-X](https://github.com/Commando-X) and securing its Kubernetes deployment using Kyverno and Open Policy Agent (OPA) Gatekeeper as Policy-as-Code tools. The goal is to deploy the VULN-BANK application and enforce organisational and compliance-aligned security policies directly within the cluster to ensure all application containers run as non-root users and automatically inject memory and CPU limits if not defined and prevent applications from running in privileged mode due to compliance with regulatory frameworks (e.g., PCI DSS or ISO 27001). 

## Two Key Policy Use-cases Implemented
-	Kyverno: Enforce that all containers run as non-root users and automatically inject CPU and memory limits if not defined.
-	OPA Gatekeeper: Prevent Pods from using hostNetwork: true or running in privileged mode, protecting the host and meeting compliance standards like PCI DSS and ISO 27001.
  
## Step-by-step Full Test Checklist 🎯
1.	Install prerequisites (Git, Docker, kubectl, kind, Helm).
2.	Clone Commando-X/vuln-bank repo and confirm Docker build & run.
3.	Create kind cluster with port mapping for application port (3000).
4.	Load the built image into kind.
5.	Create Kubernetes manifests (deployment + service) under k8s/. Deploy and verify the app (via kubectl port-forward). 
6.	Install Kyverno (Helm). Wait for pods. Apply Kyverno ClusterPolicies. Test kubectl apply of deployment.yaml (should be denied) and Kyverno should inject resources.
7.	Install Gatekeeper (Helm). Apply ConstraintTemplate and Constraint. Test bad-hostnet.yaml and bad-privileged.yaml (should be denied).
8.	Test GitHub Actions workflows for Kyverno + Gatekeeper policy violation via PR or push

## Technical Walkthrough & Setup 🚀
A detailed technical guide is posted here:

👇 Part 1, Read the Guide

(https://securitywithzee.com/posts/k8s-policy-part1/)

👇 Part 2, Read the Guide

(https://securitywithzee.com/posts/k8s-policy-part2/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
