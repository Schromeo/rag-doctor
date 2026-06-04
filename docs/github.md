# Publishing to GitHub

Create an empty GitHub repository first. Recommended settings:

- Repository name: `rag-doctor`
- Visibility: public, if you want it to be an open-source portfolio project
- Do not initialize with README, license, or `.gitignore`

Then run:

```bash
git remote add origin https://github.com/<your-user-or-org>/rag-doctor.git
git push -u origin main
```

GitHub Actions will run the test suite from `.github/workflows/ci.yml` on every push and pull request.

If you use SSH:

```bash
git remote add origin git@github.com:<your-user-or-org>/rag-doctor.git
git push -u origin main
```
