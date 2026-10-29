pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/arcved/Manual_app_deployment.git'
            }
        }

    }

    post {
        success {
            echo 'Pipeline finished successfully.'
        }

        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }

        always {
            echo "Total duration: ${currentBuild.durationString}"
        }
    }
}