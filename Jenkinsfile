
pipeline {
    agent any

    stages {
        stage('Generate Feedback') {
            steps {
                bat 'python generate_feedback.py'
            }
        }

        stage('Commit and Push') {
            steps {
                bat '''
                    git config user.name "Jenkins"
                    git config user.email "jenkins@example.com"
                    git add feedback.txt
                    git diff --cached --quiet || git commit -m "Generate feedback file"
                    git push origin HEAD:main
                '''
            }
        }
    }
}
