pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                steps{
                    git branch: 'main', url: 'https://github.com/your-username/your-repo.git'
                }
            }
        }
    }

    post {
        success { echo 'Pipeline finished successfully.' }
        failure { echo 'Pipeline failed. Check the stage logs above.' }
        always  { echo "Total duration: ${currentBuild.durationString}" }
    }
}