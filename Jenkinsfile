pipeline {
    agent any

    triggers {
        // Every Saturday at 11:59 PM in the Jenkins controller timezone.
        cron('59 23 * * 6')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout GitHub Repository') {
            steps {
                checkout scm
                bat 'git --version'
                bat 'python --version'
            }
        }

        stage('Generate Weekly Report') {
            steps {
                script {
                    env.REPORT_BUILD_STATUS = 'SUCCESS'
                }
                bat 'python generate_report.py'
            }
        }
    }

    post {
        always {
            script {
                env.REPORT_BUILD_STATUS =
                    currentBuild.currentResult ?: 'UNKNOWN'
            }

            // Generate the final report with the actual pipeline result.
            bat 'python generate_report.py'

            // Keep a copy in the Jenkins build as well.
            archiveArtifacts(
                artifacts: 'reports/*.md',
                allowEmptyArchive: true
            )

            script {
                withCredentials([
                    gitUsernamePassword(
                        credentialsId: 'github-https',
                        gitToolName: 'Default'
                    )
                ]) {
                    bat '''
                        git config user.name "Jenkins"
                        git config user.email "jenkins@example.com"
                        git add reports/
                        git diff --cached --quiet || git commit -m "Generate weekly progress report"
                        git push origin HEAD:main
                    '''
                }
            }
        }
    }
}
